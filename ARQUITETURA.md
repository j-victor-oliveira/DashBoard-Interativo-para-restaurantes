O Problema: A Dor da Maria (e do Dev)

O PROBLEMA.md descreve a Maria, que precisa de analytics flexíveis, e a FAQ.md estabelece um requisito de performance de < 500ms por query.

Para validar o desafio, o primeiro passo foi rodar as queries complexas (como as que a Maria faria) diretamente no banco de dados populado com 542.773 vendas.

O Diagnóstico (A Prova):

As queries que exigiam 3 ou 4 JOINs (ex: sales, products, channels) tiveram a seguinte performance:

Query da Maria (Top Produtos no iFood): 1.831 ms

Query de Itens (Top Complementos): 1.391 ms

Query de Entrega (Média por Bairro): 1.156 ms

Conclusão: Todas as queries falharam no requisito de < 500ms. Um dashboard que demora 2 segundos para carregar é inaceitável.

A Solução: Camada de Agregação (Materialized Views)

A minha decisão de arquitetura foi não consultar as tabelas transacionais (OLTP) diretamente. Em vez disso, criei uma camada de agregação (OLAP) usando Materialized Views do PostgreSQL.

Criei a mv_sales_analytics, que pré-calcula todos os JOINs complexos e extrai dimensões (como dia_da_semana, hora_do_dia).

Criei índices otimizados nessa view para os filtros mais comuns (canal, dia, hora).

O Resultado (A Prova da Solução):

Repeti a query mais complexa da Maria, mas desta vez consultando a mv_sales_analytics:

Performance Anterior: 1.831 ms

Performance Otimizada: 122 ms

Ganhos:

Uma melhoria de 15x na performance.

Atende facilmente ao requisito de < 500ms.

O meu Backend (API) será simples e rápido, pois só consultará esta view.

Trade-off: Os dados não são 100% "real-time" (precisam de um refresh na view, ex: a cada 5 min). Para analytics gerenciais, isso é um trade-off perfeitamente aceitável.