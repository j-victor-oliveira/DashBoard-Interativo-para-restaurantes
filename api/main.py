import os
import psycopg2
import locale
import json
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from enum import Enum
import google.generativeai as genai # Importa a biblioteca do Gemini

# Conexão com o banco de dados PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
db_conn = None

# Formata valores monetários no padrão brasileiro
# Ex: Converte 1234.56 para R$ 1.234,56
def format_currency_manual(value_str):
    """
    Formata um número (como string ou float) para o padrão BRL (R$ 1.234,56)
    sem depender do 'locale' do sistema.
    """
    try:
        value = float(value_str)
        # Formata com 2 casas decimais, usando vírgula como decimal e ponto como milhar
        formatted = "{:,.2f}".format(value)
        # Converte para o padrão BRL (troca vírgula e ponto)
        formatted_brl = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted_brl}"
    except (ValueError, TypeError):
        # Se falhar, retorna o número como string simples
        try:
            return f"R$ {float(value_str):.2f}"
        except:
            return str(value_str) 

# Configuração inicial do banco de dados
def setup_database(conn):
    """
    Prepara o banco para análises rápidas:
    - Cria views materializadas para cache de dados
    - Adiciona índices para queries mais rápidas
    - Atualiza os dados das views
    """
    print("A verificar e a criar Materialized Views...")
    try:
        with conn.cursor() as cursor:
            # 1. Criar as Views (se não existirem)
            # Usamos WITH NO DATA para as criar instantaneamente.
            cursor.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sales_analytics AS (
              SELECT
                s.id as sale_id, ps.id as product_sale_id, p.id as product_id,
                c.id as channel_id, st.id as store_id,
                p.name as product_name, c.name as channel_name,
                st.name as store_name, st.city as store_city,
                s.created_at,
                DATE(s.created_at) as sale_date,
                EXTRACT(ISODOW FROM s.created_at) as day_of_week,
                EXTRACT(HOUR FROM s.created_at) as hour_of_day,
                ps.quantity, ps.total_price as product_total_price,
                s.total_amount, s.delivery_seconds, s.sale_status_desc
              FROM sales s
              JOIN product_sales ps ON s.id = ps.sale_id
              JOIN products p ON ps.product_id = p.id
              JOIN channels c ON s.channel_id = c.id
              JOIN stores st ON s.store_id = st.id
            ) WITH NO DATA; 
            """)
            
            cursor.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_customer_analytics AS (
              SELECT
                s.customer_id, c.customer_name, c.phone_number, c.email,
                COUNT(s.id) as total_sales,
                SUM(s.total_amount) as total_revenue,
                MAX(s.created_at) as last_purchase_date
              FROM sales s
              JOIN customers c ON s.customer_id = c.id
              WHERE s.sale_status_desc = 'COMPLETED' AND s.customer_id IS NOT NULL
              GROUP BY s.customer_id, c.customer_name, c.phone_number, c.email
            ) WITH NO DATA;
            """)

            # 2. Criar Índices (se não existirem)
            # (Isto é essencial para o REFRESH CONCURRENTLY funcionar no futuro)
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uidx_mv_sales_analytics 
            ON mv_sales_analytics (sale_id, product_sale_id);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mv_sales_analytics_filters
            ON mv_sales_analytics (channel_name, day_of_week, hour_of_day, sale_status_desc, product_name);
            """)
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uidx_mv_customer_analytics
            ON mv_customer_analytics (customer_id);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mv_customer_analytics_lookup
            ON mv_customer_analytics (total_sales, last_purchase_date);
            """)

        # Salva as alterações (CREATE VIEW / CREATE INDEX)
        conn.commit()
        print("✓ Materialized Views e Índices verificados/criados com sucesso.")

    except Exception as e:
        conn.rollback() # Desfaz em caso de erro
        print(f"X Erro ao criar Views/Índices: {e}")
        raise # Para a API se não conseguir criar as views

    # 3. Atualizar (Refresh) as Views (Fora da transação principal)
    # Isto é o que preenche as views com dados.
    print("A atualizar (refresh) Materialized Views... (Isto pode demorar um momento)")
    try:
        # REFRESH não pode ser em transação, precisa de autocommit
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            # Corre o REFRESH (sem CONCURRENTLY) para o primeiro populate (CORREÇÃO DO BUG)
            cursor.execute("REFRESH MATERIALIZED VIEW mv_sales_analytics;")
            print("✓ mv_sales_analytics atualizada.")
            cursor.execute("REFRESH MATERIALIZED VIEW mv_customer_analytics;")
            print("✓ mv_customer_analytics atualizada.")
        
        # Restaura o nível de isolamento padrão
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_DEFAULT)
        print("✓ Views atualizadas com sucesso!")

    except Exception as e:
        # Se falhar, reverte para o estado padrão
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_DEFAULT) 
        print(f"X Erro durante o REFRESH das Views: {e}")
        raise # Para a API se não conseguir popular as views


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Função de 'lifespan' do FastAPI. É executada quando a API arranca.
    """
    global db_conn
    print("API a arrancar... A ligar à base de dados...")
    try:
        db_conn = psycopg2.connect(DATABASE_URL)
        
        # --- Executa o Setup do Banco de Dados ao arrancar ---
        setup_database(db_conn)
        # --- Fim do Setup ---

        print("✓ Ligação à base de dados estabelecida!")
        yield # A API fica em execução aqui
    finally:
        # Isto executa quando a API para
        if db_conn:
            db_conn.close()
            print("Ligação à base de dados fechada.")

app = FastAPI(
    title="Nola Analytics API",
    description="API para o desafio de analytics da Nola.",
    lifespan=lifespan
)

# Configuração do CORS
origins = [
    "http://localhost:3000", # Endereço do React
    # Adicione aqui os URLs do Vercel/Netlify se fizer deploy
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Opções disponíveis para análises
# Cada Enum lista as escolhas válidas que o usuário pode fazer

class MetricOptions(str, Enum):
    total_sales = "total_sales"  # Quantidade total de vendas
    total_revenue = "total_revenue"  # Valor total em R$

class GroupByOptions(str, Enum):
    product = "product"
    channel = "channel"
    store = "store"
    city = "city"
    day_of_week = "day_of_week"

class TimeBlockOptions(str, Enum):
    madrugada = "madrugada"
    manha = "manha"
    almoco = "almoco"
    tarde = "tarde"
    noite = "noite"

# Mapeamentos Seguros (Evita SQL Injection)
METRICS_MAP = {
    MetricOptions.total_sales: "COUNT(product_sale_id) AS value",
    MetricOptions.total_revenue: "SUM(product_total_price) AS value"
}

GROUP_BY_MAP = {
    GroupByOptions.product: "product_name",
    GroupByOptions.channel: "channel_name",
    GroupByOptions.store: "store_name",
    GroupByOptions.city: "store_city",
    GroupByOptions.day_of_week: "day_of_week" # O group_key será um NÚMERO
}

TIME_BLOCK_MAP = {
    TimeBlockOptions.madrugada: "hour_of_day BETWEEN 0 AND 5",
    TimeBlockOptions.manha: "hour_of_day BETWEEN 6 AND 10",
    TimeBlockOptions.almoco: "hour_of_day BETWEEN 11 AND 15",
    TimeBlockOptions.tarde: "hour_of_day BETWEEN 16 AND 18",
    TimeBlockOptions.noite: "hour_of_day BETWEEN 19 AND 23"
}

# --- Endpoints da API ---

@app.get("/")
def read_root():
    # Mensagem esperada pelos testes e documentação
    return {"message": "Bem-vindo à API de Analytics v4 (com Churn)!"}

# Endpoints para métricas de negócio

# Lista e análise de produtos
@app.get("/api/products")
def get_products():
    """
    Lista todos os produtos com suas métricas de performance:
    - Preço base e médio
    - Total de vendas e receita
    - Quantidade de clientes únicos
    """
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT 
                p.id,
                p.name,
                COALESCE(MIN(ps.base_price), 0) as base_price,
                COUNT(CASE WHEN s.sale_status_desc = 'COMPLETED' THEN ps.id END) as total_sales,
                SUM(CASE WHEN s.sale_status_desc = 'COMPLETED' THEN ps.total_price END) as total_revenue,
                AVG(CASE WHEN s.sale_status_desc = 'COMPLETED' THEN ps.total_price END) as avg_price,
                COUNT(DISTINCT CASE WHEN s.sale_status_desc = 'COMPLETED' THEN s.customer_id END) as unique_customers
            FROM products p
            LEFT JOIN product_sales ps ON p.id = ps.product_id
            LEFT JOIN sales s ON ps.sale_id = s.id
            GROUP BY p.id, p.name
            ORDER BY total_revenue DESC NULLS LAST;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Formata os valores monetários
            for result in results:
                result['base_price'] = format_currency_manual(result['base_price'])
                result['total_revenue'] = format_currency_manual(result['total_revenue'])
                result['avg_price'] = format_currency_manual(result['avg_price'])
            
            db_conn.commit()
            return {"data": results}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}/analytics")
def get_product_analytics(product_id: int):
    """
    Retorna análises detalhadas de um produto específico
    """
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Análise por período do dia
            period_query = """
            SELECT 
                CASE 
                    WHEN hour_of_day BETWEEN 0 AND 5 THEN 'Madrugada'
                    WHEN hour_of_day BETWEEN 6 AND 10 THEN 'Manhã'
                    WHEN hour_of_day BETWEEN 11 AND 15 THEN 'Almoço'
                    WHEN hour_of_day BETWEEN 16 AND 18 THEN 'Tarde'
                    ELSE 'Noite'
                END as period,
                COUNT(*) as sales_count,
                SUM(product_total_price) as total_revenue
            FROM mv_sales_analytics
            WHERE product_id = %s AND sale_status_desc = 'COMPLETED'
            GROUP BY period
            ORDER BY sales_count DESC;
            """
            cursor.execute(period_query, (product_id,))
            period_results = cursor.fetchall()
            
            # Análise por canal
            channel_query = """
            SELECT 
                channel_name,
                COUNT(*) as sales_count,
                SUM(product_total_price) as total_revenue
            FROM mv_sales_analytics
            WHERE product_id = %s AND sale_status_desc = 'COMPLETED'
            GROUP BY channel_name
            ORDER BY sales_count DESC;
            """
            cursor.execute(channel_query, (product_id,))
            channel_results = cursor.fetchall()
            
            # Formata valores monetários
            for result in period_results + channel_results:
                if 'total_revenue' in result:
                    result['total_revenue'] = format_currency_manual(result['total_revenue'])
            
            db_conn.commit()
            return {
                "period_analysis": period_results,
                "channel_analysis": channel_results
            }
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpi/total_revenue")
def get_kpi_total_revenue():
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT SUM(total_amount) as value FROM sales WHERE sale_status_desc = 'COMPLETED';")
            result = cursor.fetchone()
            db_conn.commit()
            
            # Usa a nova função de formatação manual
            formatted_value = format_currency_manual(result['value'])
            return {"label": "Faturação Total", "value": formatted_value}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpi/avg_ticket")
def get_kpi_avg_ticket():
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT AVG(total_amount) as value FROM sales WHERE sale_status_desc = 'COMPLETED' AND total_amount > 0;")
            result = cursor.fetchone()
            db_conn.commit()
            
            # Usa a nova função de formatação manual
            formatted_value = format_currency_manual(result['value'])
            return {"label": "Ticket Médio", "value": formatted_value}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpi/total_sales_count")
def get_kpi_total_sales_count():
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT COUNT(id) as value FROM sales WHERE sale_status_desc = 'COMPLETED';")
            result = cursor.fetchone()
            db_conn.commit()
            
            # Formata como número (ex: 532.654)
            formatted_value = f"{int(result['value']):,}".replace(",", ".")
            return {"label": "Total de Vendas", "value": formatted_value}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Análises flexíveis de dados
@app.get("/api/analytics")
def get_analytics(
    metric: MetricOptions,  # Qual métrica analisar (vendas ou faturamento)
    group_by: GroupByOptions,  # Como agrupar (produto, canal, etc)
    channel: Optional[str] = None,  # Filtro de canal específico
    day_of_week: Optional[int] = Query(None, ge=1, le=7),  # Dia da semana (1=Seg, 7=Dom)
    time_block: Optional[TimeBlockOptions] = None  # Período do dia
):
    """
    Gera análises customizadas dos dados de vendas:
    - Agrupa dados por diferentes dimensões
    - Permite filtros específicos
    - Retorna os top 20 resultados
    """
    selected_metric = METRICS_MAP[metric]
    selected_group_by = GROUP_BY_MAP[group_by]

    # Constrói a query base
    query = f"""
        SELECT
            {selected_group_by} AS group_key,
            {selected_metric}
        FROM
            mv_sales_analytics
        WHERE
            sale_status_desc = 'COMPLETED'
    """
    
    # Lista de parâmetros para evitar SQL Injection
    params = []

    # Adiciona filtros dinâmicos de forma segura
    if channel:
        query += " AND channel_name = %s"
        params.append(channel)
    if day_of_week:
        query += " AND day_of_week = %s"
        params.append(day_of_week)
    if time_block:
        # Seguro, pois 'time_block' é validado pelo Enum
        query += f" AND {TIME_BLOCK_MAP[time_block]}" 

    # Finaliza a query
    query += f" GROUP BY {selected_group_by} ORDER BY value DESC LIMIT 20;"

    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            db_conn.commit()
        return {"data": results}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro de base de dados: {e}")

# --- Endpoint de Clientes em Risco (Corrigido) ---

@app.get("/api/churn-customers")
def get_churn_customers():
    """
    Consulta a Materialized View de clientes para encontrar clientes em risco.
    """
    query = """
        SELECT 
            customer_name,
            phone_number,
            email,
            total_sales,
            total_revenue,
            last_purchase_date
        FROM 
            mv_customer_analytics
        WHERE 
            total_sales >= 3
            AND last_purchase_date <= (CURRENT_DATE - INTERVAL '30 days')
        ORDER BY 
            last_purchase_date ASC;
    """
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            db_conn.commit()
        # Retorna a lista diretamente (os testes esperam uma lista JSON)
        return results
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro de base de dados: {e}")

# --- Endpoints de Relatórios ---

@app.get("/api/reports/sales-summary")
def get_sales_summary(
    start_date: str = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Data final (YYYY-MM-DD)")
):
    """
    Gera um relatório resumido de vendas por período, 
    enviando valores numéricos puros para o frontend formatar
    """
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT 
                DATE(created_at) as sale_date,
                COUNT(DISTINCT sale_id) as total_orders,
                COUNT(product_sale_id) as total_items_sold,
                ROUND(CAST(SUM(product_total_price) as numeric), 2) as total_revenue,
                AVG(delivery_seconds) as avg_delivery_time
            FROM mv_sales_analytics
            WHERE sale_status_desc = 'COMPLETED'
            """
            params = []
            
            if start_date:
                query += " AND DATE(created_at) >= %s"
                params.append(start_date)
            if end_date:
                query += " AND DATE(created_at) <= %s"
                params.append(end_date)
                
            query += " GROUP BY DATE(created_at) ORDER BY sale_date ASC;"
            
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            
            # Formata apenas o tempo de entrega, deixa o valor monetário como número
            for result in results:
                if result['avg_delivery_time']:
                    minutes = int(result['avg_delivery_time'] / 60)
                    result['avg_delivery_time'] = f"{minutes} minutos"
            
            db_conn.commit()
            return {"data": results}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/product-performance")
def get_product_performance(
    start_date: str = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Data final (YYYY-MM-DD)")
):
    """
    Gera um relatório de performance dos produtos
    """
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            WITH product_stats AS (
                SELECT 
                    product_id,
                    product_name,
                    COUNT(DISTINCT sale_id) as order_count,
                    COUNT(product_sale_id) as quantity_sold,
                    SUM(product_total_price) as total_revenue,
                    AVG(product_total_price) as avg_price
                FROM mv_sales_analytics
                WHERE sale_status_desc = 'COMPLETED'
            """
            params = []
            
            if start_date:
                query += " AND DATE(created_at) >= %s"
                params.append(start_date)
            if end_date:
                query += " AND DATE(created_at) <= %s"
                params.append(end_date)
                
            query += """
                GROUP BY product_id, product_name
            ),
            rankings AS (
                SELECT 
                    *,
                    RANK() OVER (ORDER BY total_revenue DESC) as revenue_rank,
                    RANK() OVER (ORDER BY quantity_sold DESC) as quantity_rank
                FROM product_stats
            )
            SELECT 
                product_name,
                order_count,
                quantity_sold,
                total_revenue,
                avg_price,
                revenue_rank,
                quantity_rank
            FROM rankings
            ORDER BY revenue_rank;
            """
            
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            
            # Formata valores monetários
            for result in results:
                result['total_revenue'] = format_currency_manual(result['total_revenue'])
                result['avg_price'] = format_currency_manual(result['avg_price'])
            
            db_conn.commit()
            return {"data": results}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/channel-performance")
def get_channel_performance(
    start_date: str = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Data final (YYYY-MM-DD)")
):
    """
    Gera um relatório de performance por canal
    """
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT 
                channel_name,
                COUNT(DISTINCT sale_id) as total_orders,
                COUNT(product_sale_id) as total_items,
                SUM(product_total_price) as total_revenue,
                AVG(delivery_seconds) / 60.0 as avg_delivery_minutes,
                COUNT(DISTINCT CASE WHEN delivery_seconds > 2700 THEN sale_id END) as delayed_orders
            FROM mv_sales_analytics
            WHERE sale_status_desc = 'COMPLETED'
            """
            params = []
            
            if start_date:
                query += " AND DATE(created_at) >= %s"
                params.append(start_date)
            if end_date:
                query += " AND DATE(created_at) <= %s"
                params.append(end_date)
                
            query += " GROUP BY channel_name ORDER BY total_revenue DESC;"
            
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            
            # Formata valores
            for result in results:
                result['total_revenue'] = format_currency_manual(result['total_revenue'])
                avg_minutes = result.pop('avg_delivery_minutes', None)
                if avg_minutes is not None:
                    result['avg_delivery_time'] = f"{avg_minutes:.1f} minutos"
                else:
                    result['avg_delivery_time'] = "-"
            
            db_conn.commit()
            return {"data": results}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Sistema de insights inteligentes

def get_dynamic_mock_insight(data: List[dict], context: str) -> str:
    """
    Analisa os dados e gera insights práticos:
    - Identifica padrões importantes
    - Sugere ações concretas
    - Alerta sobre problemas
    - Destaca oportunidades
    """
    if not data:
        return "Não há dados suficientes para gerar uma análise."

    # Converte números dos dias para nomes mais amigáveis
    day_map = {1: "Segunda-feira", 2: "Terça-feira", 3: "Quarta-feira", 
               4: "Quinta-feira", 5: "Sexta-feira", 6: "Sábado", 7: "Domingo"}

    # Soma total para calcular porcentagens
    total_sum = sum(item.get('value', 0) for item in data)
    if total_sum == 0:
        return "Não há valores para analisar no período selecionado."

    # Calcula percentuais e médias
    for item in data:
        item['percentage'] = (item.get('value', 0) / total_sum) * 100

    # Identifica itens principais
    top_items = data[:3]  # Top 3
    bottom_items = data[-3:]  # Bottom 3
    
    insights = []
    recommendations = []
    
    if context == 'channel':
        # Análise específica para canais de venda
        main_channel = top_items[0]
        main_channel_share = main_channel['percentage']
        
        insights.append("📊 Distribuição dos Canais")
        insights.append(f"• O canal '{main_channel['group_key']}' representa {main_channel_share:.1f}% das vendas ({main_channel['value']:,} pedidos)")
        
        # Analisa concentração de canais
        if main_channel_share > 70:
            insights.append("\n⚠️ Alerta de Concentração")
            insights.append("• Há uma dependência muito alta de um único canal")
            
            recommendations.append("\n🎯 Ações Recomendadas")
            recommendations.append("1. Diversifique os canais de venda para reduzir riscos")
            recommendations.append("2. Desenvolva seu canal próprio para reduzir custos com comissões")
            if any(c['group_key'] in ['iFood', 'Rappi', 'Uber Eats'] for c in data):
                recommendations.append("3. Crie promoções exclusivas no App Próprio/WhatsApp")
        
        # Analisa oportunidades em canais específicos
        delivery_channels = [c for c in data if c['group_key'] in ['iFood', 'Rappi', 'Uber Eats']]
        if delivery_channels:
            total_delivery = sum(c['value'] for c in delivery_channels)
            insights.append(f"\n📱 Apps de Delivery")
            insights.append(f"• Representam {total_delivery:,} pedidos")
            
        # Analisa canal próprio se existir
        own_channels = [c for c in data if c['group_key'] in ['App Próprio', 'WhatsApp', 'Site Próprio']]
        if own_channels:
            total_own = sum(c['value'] for c in own_channels)
            insights.append(f"\n🏠 Canais Próprios")
            insights.append(f"• Geram {total_own:,} pedidos")
            
        # Adiciona recomendações específicas se não houver alerta de concentração
        if main_channel_share <= 70:
            recommendations.append("\n💡 Oportunidades de Crescimento")
            recommendations.append("1. Fortaleça a presença nos canais mais rentáveis")
            recommendations.append("2. Analise o perfil de cliente de cada canal")
            recommendations.append("3. Adapte o cardápio para cada plataforma")

    elif context == 'day_of_week':
        # Análise específica para dias da semana
        peak_day = day_map.get(int(top_items[0]['group_key']), 'N/A')
        peak_value = top_items[0]['value']
        slowest_day = day_map.get(int(bottom_items[0]['group_key']), 'N/A')
        
        # Calcula variação entre dias
        daily_variation = (peak_value - bottom_items[0]['value']) / bottom_items[0]['value'] * 100
        
        insights.append("📅 Padrões Semanais")
        insights.append(f"• Dia mais movimentado: {peak_day} ({peak_value:,} pedidos)")
        insights.append(f"• Dia mais fraco: {slowest_day}")
        insights.append(f"• Variação: {daily_variation:.1f}% entre pico e vale")
        
        # Identifica padrões de fim de semana vs. dias úteis
        weekend_data = [d for d in data if int(d['group_key']) in [6,7]]
        weekday_data = [d for d in data if int(d['group_key']) not in [6,7]]
        
        if weekend_data and weekday_data:
            avg_weekend = sum(d['value'] for d in weekend_data) / len(weekend_data)
            avg_weekday = sum(d['value'] for d in weekday_data) / len(weekday_data)
            weekend_diff = ((avg_weekend / avg_weekday) - 1) * 100
            
            insights.append("\n🔄 Comparativo Fim de Semana")
            if weekend_diff > 0:
                insights.append(f"• Volume {weekend_diff:.1f}% maior que dias úteis")
            else:
                insights.append(f"• Volume {abs(weekend_diff):.1f}% menor que dias úteis")
        
        # Recomendações específicas por padrão
        recommendations.append("\n🎯 Estratégias Sugeridas")
        
        # Base nas variações diárias
        if daily_variation > 50:
            recommendations.append(f"1. Lance promoções especiais para {slowest_day}")
            recommendations.append(f"2. Crie um 'Dia Especial' com descontos progressivos")
            recommendations.append("3. Ajuste a equipe conforme o movimento de cada dia")
        else:
            recommendations.append("1. Mantenha a consistência atual de operação")
            recommendations.append("2. Foque em aumentar o ticket médio em dias de pico")
            recommendations.append("3. Desenvolva menu especial para dias mais movimentados")
        
        # Sugestões específicas para fim de semana
        if weekend_data and weekday_data:
            recommendations.append("\n💡 Dicas Adicionais")
            if weekend_diff > 20:
                recommendations.append("• Crie pacotes especiais para dias úteis")
                recommendations.append("• Avalie ampliar a equipe nos fins de semana")
            elif weekend_diff < -20:
                recommendations.append("• Desenvolva atrativos para fins de semana")
                recommendations.append("• Considere promoções familiares aos sábados/domingos")

    elif context == 'product':
        # Análise específica para produtos
        top_product = top_items[0]
        insights.append("🏆 Produtos em Destaque")
        
        # Análise do produto mais vendido
        product_name = top_product['group_key'].lower()
        product_type = "outro"
        
        if "burger" in product_name or "x-" in product_name:
            product_type = "hamburguer"
        elif "combo" in product_name:
            product_type = "combo"
        elif "pizza" in product_name:
            product_type = "pizza"
        elif any(word in product_name for word in ['bebida', 'suco', 'refri']):
            product_type = "bebida"
        
        insights.append(f"• Líder: '{top_product['group_key']}' ({top_product['value']:,} vendas)")
        insights.append(f"• Representa {top_product['percentage']:.1f}% das vendas totais")
        
        # Análise de concentração
        if top_product['percentage'] > 30:
            insights.append("\n⚠️ Alerta: Alta dependência de um único produto")
        
        # Recomendações sempre presentes baseadas no tipo de produto
        recommendations.append("\n🎯 Estratégias Sugeridas")
        
        # Estratégias específicas por tipo de produto
        if product_type == "hamburguer":
            recommendations.append("1. Crie uma versão premium com ingredientes especiais")
            recommendations.append("2. Desenvolva uma versão vegetariana/vegana")
            recommendations.append("3. Monte um combo exclusivo com este hambúrguer")
        elif product_type == "combo":
            recommendations.append("1. Adicione opções de personalização ao combo")
            recommendations.append("2. Crie uma versão família deste combo")
            recommendations.append("3. Ofereça um desconto progressivo para mais unidades")
        elif product_type == "pizza":
            recommendations.append("1. Desenvolva uma versão em tamanho família")
            recommendations.append("2. Crie um combo com bebidas e sobremesa")
            recommendations.append("3. Ofereça bordas especiais como diferencial")
        elif product_type == "bebida":
            recommendations.append("1. Crie combos com os lanches mais vendidos")
            recommendations.append("2. Ofereça desconto na segunda unidade")
            recommendations.append("3. Desenvolva uma versão exclusiva ou sabor da casa")
        else:
            recommendations.append("1. Analise o diferencial deste produto")
            recommendations.append("2. Crie variações baseadas no mesmo conceito")
            recommendations.append("3. Desenvolva combos exclusivos")
        
        # Análise complementar de oportunidades
        second_place = top_items[1] if len(top_items) > 1 else None
        if second_place:
            diff_to_leader = top_product['value'] - second_place['value']
            if diff_to_leader > 0:
                recommendations.append(f"\n💡 Dica: O segundo colocado vende {diff_to_leader} unidades a menos")
                recommendations.append("• Analise o que faz o líder ter tanto destaque")
        
        # Análise dos produtos com baixo desempenho
        low_performers = [p for p in data if p['percentage'] < 1]
        if low_performers:
            insights.append(f"\n📉 Produtos com Baixo Desempenho")
            insights.append(f"• {len(low_performers)} produtos representam menos de 1% das vendas cada")
            recommendations.append("\n⚠️ Ações Corretivas")
            recommendations.append("• Considere remover ou reformular itens de baixa saída")
            recommendations.append("• Avalie a visibilidade destes produtos no cardápio")
            recommendations.append("• Teste promoções para validar o potencial")

    else:  # Análise genérica para outros contextos
        insights.append(f"📊 **Análise Geral:**")
        for item in top_items:
            insights.append(f"• {item['group_key']}: {item['value']:,} ({item['percentage']:.1f}%)")
        
        recommendations.append("🎯 **Recomendações:**")
        recommendations.append("1. Analise os fatores de sucesso dos líderes")
        recommendations.append("2. Identifique oportunidades de melhoria nos itens de menor desempenho")

    # Monta o resultado final com formatação limpa
    sections = []
    
    # Título principal
    sections.append("💡 Análise Detalhada\n")
    
    # Seção de insights
    if insights:
        sections.append("\n".join(insights))
    
    # Seção de recomendações
    if recommendations:
        sections.append("\n".join(recommendations))
    
    # Une todas as seções com espaçamento adequado
    result = "\n\n".join(section for section in sections if section)
    
    return result


    return f"""
    💡 **Insight da IA:**
    
    Analisando os dados por **{context.upper()}**:
    
    1. {insight_1}
    
    2. {insight_2}
    """

@app.post("/api/insight/gemini")
async def get_gemini_insight(
    # Recebe os dados E o contexto do frontend
    body: dict = Body(...)
):
    """
    Recebe os dados de um relatório e o contexto (groupBy)
    e usa uma lógica "mock" inteligente para gerar um insight.
    """
    data = body.get("data")
    context = body.get("context") # 'product', 'city', 'day_of_week', etc.
    
    if not data or not context:
        raise HTTPException(status_code=400, detail="Dados ou contexto em falta.")

    # --- MOCK DE RESPOSTA (PARA A DEMO) ---
    # Usamos a nossa nova função "contextual" para gerar
    # uma resposta que é dinâmica e relevante.
    
    insight_text = get_dynamic_mock_insight(data, context)
    
    return {"insight": insight_text}
    
    # --- CÓDIGO REAL DO GEMINI (Para quando tiver uma API Key) ---
    # (Não descomente isto a menos que tenha uma API Key válida)
    
    # try:
    #     model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
    #     data_json = json.dumps(data)
    #     prompt = f"""
    #         Você é um analista de dados especialista em restaurantes, a falar com a Dona Maria (a dona).
    #         O relatório atual é agrupado por: {context}.
    #         Baseado nos seguintes dados (em formato JSON) do relatório:
    #         {data_json}
            
    #         Por favor, escreva 2 insights curtos e acionáveis (em bullet points) para ela.
    #         Seja direto e amigável. Comece com "💡 **Insight da IA:**"
    #     """
    #     response = await model.generate_content_async(prompt)
    #     return {"insight": response.text}
    # except Exception as e:
    ...

