import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import Products from './components/Products';
import Reports from './components/Reports';
import './components/components.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import './App.css';

// Registra componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// --- CORREÇÃO: ADICIONAR A FUNÇÃO QUE FOI APAGADA ---
// Helper para formatar moeda (usado na Tabela de Churn)
function format_currency(value) {
  if (value == null) return "N/A";
  // Assegura que o valor é um número antes de formatar
  const numberValue = Number(value);
  if (isNaN(numberValue)) return "N/A";
  
  return new Intl.NumberFormat('pt-BR', { 
    style: 'currency', 
    currency: 'BRL' 
  }).format(numberValue);
}
// --- FIM DA CORREÇÃO ---


// --- Constantes de Opções para os Dropdowns ---

const metricOptions = [
  { value: 'total_sales', label: 'Vendas Totais (Qtd)' },
  { value: 'total_revenue', label: 'Faturação (R$)' },
];

const groupByOptions = [
  { value: 'product', label: 'Produto' },
  { value: 'channel', label: 'Canal' },
  { value: 'store', label: 'Loja' },
  { value: 'city', label: 'Cidade' },
  { value: 'day_of_week', label: 'Dia da Semana' },
];

const channelOptions = [
  { value: '', label: 'Todos os Canais' },
  { value: 'Presencial', label: 'Presencial' },
  { value: 'iFood', label: 'iFood' },
  { value: 'Rappi', label: 'Rappi' },
  { value: 'Uber Eats', label: 'Uber Eats' },
  { value: 'WhatsApp', label: 'WhatsApp' },
  { value: 'App Próprio', label: 'App Próprio' },
];

const dayOfWeekOptions = [
  { value: '', label: 'Todos os Dias' },
  { value: '1', label: 'Segunda-feira' },
  { value: '2', label: 'Terça-feira' },
  { value: '3', label: 'Quarta-feira' },
  { value: '4', label: 'Quinta-feira' },
  { value: '5', label: 'Sexta-feira' },
  { value: '6', label: 'Sábado' },
  { value: '7', label: 'Domingo' },
];

// Esta lista está agora 100% sincronizada com a API (api/main.py)
const timeBlockOptions = [
  { value: '', label: 'Dia Inteiro' },
  { value: 'madrugada', label: 'Madrugada (0h-6h)' },
  { value: 'manha', label: 'Manhã (6h-11h)' },
  { value: 'almoco', label: 'Almoço (11h-15h)' },
  { value: 'tarde', label: 'Tarde (15h-19h)' },
  { value: 'noite', label: 'Noite (19h-23h)' },
];

// --- Componente: KPI Card ---
function KpiCard({ title, endpoint }) {
  const [data, setData] = useState({ label: title, value: '...' });
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchKpi() {
      try {
        // A API agora devolve um JSON com { value: "R$ 123,45" }
        const response = await axios.get(`http://localhost:8000${endpoint}`);
        setData(response.data);
      } catch (err) {
        console.error(`Erro ao carregar KPI: ${endpoint}`, err);
        setError("Erro");
        setData({ label: title, value: 'N/A' });
      }
    }
    fetchKpi();
  }, [title, endpoint]);

  return (
    <div className="kpi-card">
      <span className="kpi-title">{data.label}</span>
      <span className="kpi-value">{data.value}</span>
      {error && <span className="kpi-error">{error}</span>}
    </div>
  );
}

// --- Componente: Dashboard ---
function Dashboard() {
  const [metric, setMetric] = useState('total_sales');
  const [groupBy, setGroupBy] = useState('product');
  const [channel, setChannel] = useState('');
  const [dayOfWeek, setDayOfWeek] = useState('');
  const [timeBlock, setTimeBlock] = useState(''); 
  
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartTitle, setChartTitle] = useState('Relatório Principal');

  // Para o Insight de IA
  const [insight, setInsight] = useState("");
  const [insightLoading, setInsightLoading] = useState(false);

  const metricLabel = metricOptions.find(m => m.value === metric)?.label || '';
  const groupLabel = groupByOptions.find(g => g.value === groupBy)?.label || '';

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    setChartData(null);
    setInsight(""); // Limpa o insight anterior
    setInsightLoading(false);

    const params = new URLSearchParams({
      metric: metric,
      group_by: groupBy,
    });

    if (channel) params.append('channel', channel);
    if (dayOfWeek) params.append('day_of_week', dayOfWeek);
    if (timeBlock) params.append('time_block', timeBlock); 
    
    setChartTitle(`${metricLabel} por ${groupLabel}`);

    try {
      const response = await axios.get(`http://localhost:8000/api/analytics?${params.toString()}`);
      const apiData = response.data.data;

      let labelMap = null;
      if (groupBy === 'day_of_week') {
        labelMap = new Map(dayOfWeekOptions.map(d => [parseInt(d.value), d.label]));
      }

      const dataForChart = {
        // Prepara os dados para o Chart.js
        labels: apiData.map(item => 
          labelMap ? (labelMap.get(item.group_key) || item.group_key) : item.group_key
        ),
        datasets: [
          {
            label: metricLabel,
            data: apiData.map(item => item.value),
            backgroundColor: '#FF5A5F', // Cor da Nola
            borderColor: '#FF5A5F',
            borderRadius: 4,
          },
        ],
        rawData: apiData // Guarda os dados brutos para enviar ao Gemini
      };
      
      setChartData(dataForChart);
      if (apiData.length === 0) {
        setError("Nenhum dado encontrado para esta combinação de filtros.");
      }

    } catch (err) {
      console.error("Erro a chamar API:", err);
      // Pega a mensagem de erro específica do FastAPI (para erros 422)
      const errorMsg = err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || err.message;
      setError(`Não foi possível carregar os dados: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  // --- Função para chamar a IA do Gemini ---
  const fetchInsight = async () => {
    if (!chartData || !chartData.rawData) {
      alert("Por favor, gere um gráfico primeiro.");
      return;
    }
    
    setInsightLoading(true);
    setInsight(""); // Limpa o insight antigo
    
    try {
      // --- CORREÇÃO IA: Envia os dados E o contexto (groupBy) ---
      const payload = {
        data: chartData.rawData,
        context: groupBy // Envia 'product', 'city', 'day_of_week', etc.
      };
      
      const response = await axios.post('http://localhost:8000/api/insight/gemini', payload);
      // Converte quebras de linha (\\n) em <br> para o HTML
      const formattedInsight = response.data.insight.replace(/\n/g, '<br />');
      setInsight(formattedInsight);
    } catch (err) {
      console.error("Erro ao chamar API do Gemini:", err);
      setInsight("Não foi possível gerar o insight de IA. Verifique a API.");
    } finally {
      setInsightLoading(false);
    }
  };

  return (
    <>
      <div className="kpi-grid">
        <KpiCard title="Faturação Total" endpoint="/api/kpi/total_revenue" />
        <KpiCard title="Ticket Médio" endpoint="/api/kpi/avg_ticket" />
        <KpiCard title="Total de Vendas" endpoint="/api/kpi/total_sales_count" />
      </div>

      <div className="filter-bar card">
        <label>
          Ver:
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>
            {metricOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label>
          Agrupar por:
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
            {groupByOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
        
        <label>
          Canal:
          <select value={channel} onChange={(e) => setChannel(e.target.value)}>
            {channelOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label>
          Dia da Semana:
          <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)}>
            {dayOfWeekOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label>
          Período do Dia:
          <select value={timeBlock} onChange={(e) => setTimeBlock(e.target.value)}>
            {timeBlockOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        {/* --- CORREÇÃO: Botão "Gerar" Adicionado de Volta --- */}
        <button onClick={fetchData} disabled={loading} className="generate-button">
          {loading ? '...' : 'Gerar'}
        </button>
      </div>

      <div className="chart-container card">
        <h2 className="chart-title">{chartTitle}</h2>
        {error && <p className="error-message">{error}</p>}
        {loading && <p>A carregar gráfico...</p>}
        {!loading && !error && !chartData && <p className="placeholder-text">Selecione os filtros e clique em "Gerar" para ver o relatório.</p>}
        {chartData && (
          <div className="chart-wrapper">
            <Bar 
              data={chartData} 
              options={{ 
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  y: { ticks: { color: '#373F51' } },
                  x: { ticks: { color: '#373F51' } },
                }
              }} 
            />
          </div>
        )}
        
        {/* --- Botão e Card da IA (Gemini) --- */}
        {!loading && chartData && (
          <div className="insight-section">
            <button onClick={fetchInsight} disabled={insightLoading} className="insight-button">
              {insightLoading ? 'A pensar...' : '🤖 Gerar Análise com IA'}
            </button>
            {insightLoading && <p>A IA está a analisar os dados...</p>}
            {insight && (
              <div className="insight-card" dangerouslySetInnerHTML={{ __html: insight }} />
            )}
          </div>
        )}
      </div>
    </>
  );
}

// --- Componente: Clientes em Risco ---
function ChurnReport() {
  const [churnData, setChurnData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchChurnData() {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get('http://localhost:8000/api/churn-customers');
        const customers = Array.isArray(response.data)
          ? response.data
          : Array.isArray(response.data?.data)
            ? response.data.data
            : [];

        setChurnData(customers); // Guarda os clientes em risco
        if (customers.length === 0) {
          setError("Nenhum cliente encontrado. Boas notícias!");
        }
      } catch (err) {
        console.error("Erro ao carregar relatório de churn:", err);
        setError("Não foi possível carregar o relatório. Verifique a API.");
      } finally {
        setLoading(false);
      }
    }
    fetchChurnData();
  }, []);

  // Formata a data (ex: 2025-10-29T...) para 29/10/2025
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR', { timeZone: 'UTC' });
    } catch (e) {
      return dateString;
    }
  };

  return (
    <div className="card">
      <h2>Clientes em Risco de Churn</h2>
      <p>Clientes que compraram 3 ou mais vezes, mas não compram há mais de 30 dias.</p>
      
      {loading && <p>A carregar relatório...</p>}
      
      {error && !loading && (
        <p className="placeholder-text">{error}</p>
      )}
      
      {!loading && !error && churnData.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Nome do Cliente</th>
                <th>Contacto</th>
                <th>Total de Vendas</th>
                <th>Faturação Total</th>
                <th>Última Compra</th>
              </tr>
            </thead>
            <tbody>
              {churnData.map((customer, index) => (
                <tr key={index}>
                  <td>{customer.customer_name}</td>
                  <td>{customer.phone_number || customer.email || 'N/D'}</td>
                  <td>{customer.total_sales}</td>
                  {/* A função format_currency está agora visível */}
                  <td className="currency">{format_currency(customer.total_revenue)}</td>
                  <td>{formatDate(customer.last_purchase_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// --- Componente Principal da App ---
function App() {
  // Define 'dashboard' como a página inicial
  const [page, setPage] = useState('dashboard'); 

  // Atualiza a página com base no Hash (ex: #dashboard, #churn)
  useEffect(() => {
    const handleHashChange = () => {
      // Limpa o '#' e define a página, ou 'dashboard' se for vazio
      const hash = window.location.hash.replace('#', '');
      setPage(hash || 'dashboard');
    };
    
    // Ouve as mudanças no URL
    window.addEventListener('hashchange', handleHashChange);
    // Define a página inicial com base no URL atual
    handleHashChange(); 
    
    // Limpa o listener quando o componente é destruído
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []); // [] = Executa apenas uma vez, ao arrancar


  const renderPage = () => {
    switch(page) {
      case 'dashboard':
        return <Dashboard />;
      case 'churn':
        return <ChurnReport />;
      case 'produtos':
        return <Products />;
      case 'relatorios':
        return <Reports />;
      default:
        // Se o URL for inválido (ex: #qualquercoisa), vai para o dashboard
        return <Dashboard />;
    }
  };

  // Alerta para links de placeholder
  const handlePlaceholderClick = (e, pageName) => {
    e.preventDefault();
    alert(`A página "${pageName}" é um placeholder para este MVP. Implementei o "Dashboard" e "Clientes em Risco" como prova de conceito. A funcionalidade de IA está no botão 'Gerar Análise' dentro do Dashboard.`);
  };

  return (
    <div className="app-container">
      {/* --- Sidebar (Barra Lateral) --- */}
      <nav className="sidebar">
        <div className="sidebar-header">
          <span className="logo">nola</span>
        </div>
        <ul className="sidebar-menu">
          {/* O 'active' é agora controlado pelo estado 'page' */}
          <li className={page === 'dashboard' ? 'active' : ''}>
            <a href="#dashboard"> {/* onClick foi removido, agora usa o URL hash */}
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/></svg>
              Dashboard
            </a>
          </li>
          <li className={page === 'churn' ? 'active' : ''}>
            <a href="#churn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              Clientes em Risco
            </a>
          </li>
          <li className={page === 'relatorios' ? 'active' : ''}>
            <a href="#relatorios">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              Relatórios
            </a>
          </li>
          <li className={page === 'produtos' ? 'active' : ''}>
            <a href="#produtos">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
              Produtos
            </a>
          </li>
        </ul>
      </nav>

      {/* --- Conteúdo Principal (Layout Corrigido) --- */}
      <main className="main-content">
        <header className="header">
          <div className="header-title">
            Dona Maria / <span className="page-title">
              {/* O título agora também é dinâmico com base no estado 'page' */}
              {page === 'dashboard' ? 'Dashboard' : 
               page === 'churn' ? 'Clientes em Risco' : 
               page.charAt(0).toUpperCase() + page.slice(1)}
            </span>
          </div>
          <div className="user-profile" onClick={(e) => handlePlaceholderClick(e, 'Perfil do Utilizador')}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span>Dona Maria</span>
          </div>
        </header>

        {/* Renderiza a página ativa dentro da área de scroll */}
        <div className="page-content">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}

export default App;

