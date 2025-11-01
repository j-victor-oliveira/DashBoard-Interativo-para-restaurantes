import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Registra os componentes necessários do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function DateRangePicker({ startDate, endDate, onStartChange, onEndChange }) {
  return (
    <div className="date-range">
      <label>
        De:
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartChange(e.target.value)}
        />
      </label>
      <label>
        Até:
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndChange(e.target.value)}
        />
      </label>
    </div>
  );
}

function SalesSummary({ startDate, endDate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchSummary() {
      try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const response = await axios.get(`http://localhost:8000/api/reports/sales-summary?${params}`);
        setData(response.data.data);
      } catch (err) {
        setError('Erro ao carregar resumo de vendas');
      } finally {
        setLoading(false);
      }
    }

    fetchSummary();
  }, [startDate, endDate]);

  if (loading) return <div>Carregando resumo...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!data || data.length === 0) return <div>Nenhum dado encontrado para o período selecionado.</div>;

  const chartData = {
    labels: data.map(d => d.sale_date),
    datasets: [
      {
        label: 'Faturação',
        data: data.map(d => d.total_revenue),
        borderColor: '#FF5A5F',
        backgroundColor: 'rgba(255, 90, 95, 0.1)',
        yAxisID: 'y',
        fill: true
      },
      {
        label: 'Pedidos',
        data: data.map(d => d.total_orders),
        borderColor: '#373F51',
        backgroundColor: 'rgba(55, 63, 81, 0.1)',
        yAxisID: 'y1',
        fill: true
      }
    ]
  };

  return (
    <div className="sales-summary card">
      <h3>Resumo de Vendas</h3>
      <div className="chart-container">
        <Line
          data={chartData}
          options={{
            responsive: true,
            interaction: {
              mode: 'index',
              intersect: false,
            },
                scales: {
              y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                  display: true,
                  text: 'Faturação (R$)'
                },
                ticks: {
                  callback: function(value) {
                    return 'R$ ' + value.toLocaleString('pt-BR');
                  }
                }
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                  display: true,
                  text: 'Número de Pedidos'
                },
                grid: {
                  drawOnChartArea: false,
                }
              }
            }
          }}
        />
      </div>
    </div>
  );
}

function ProductPerformance({ startDate, endDate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchPerformance() {
      try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const response = await axios.get(`http://localhost:8000/api/reports/product-performance?${params}`);
        setData(response.data.data);
      } catch (err) {
        setError('Erro ao carregar performance dos produtos');
      } finally {
        setLoading(false);
      }
    }

    fetchPerformance();
  }, [startDate, endDate]);

  if (loading) return <div>Carregando performance...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!data || data.length === 0) return <div>Nenhum dado encontrado para o período selecionado.</div>;

  // Pega apenas os top 10 produtos
  const top10 = data.slice(0, 10);

  const chartData = {
    labels: top10.map(d => d.product_name),
    datasets: [
      {
        label: 'Quantidade Vendida',
        data: top10.map(d => d.quantity_sold),
        backgroundColor: '#FF5A5F',
      }
    ]
  };

  return (
    <div className="product-performance card">
      <h3>Performance dos Produtos (Top 10)</h3>
      <div className="chart-container">
        <Bar
          data={chartData}
          options={{
            indexAxis: 'y',
            responsive: true,
            plugins: {
              legend: {
                display: false
              }
            }
          }}
        />
      </div>
    </div>
  );
}

function ChannelPerformance({ startDate, endDate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchPerformance() {
      try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const response = await axios.get(`http://localhost:8000/api/reports/channel-performance?${params}`);
        setData(response.data.data);
      } catch (err) {
        setError('Erro ao carregar performance dos canais');
      } finally {
        setLoading(false);
      }
    }

    fetchPerformance();
  }, [startDate, endDate]);

  if (loading) return <div>Carregando performance...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!data || data.length === 0) return <div>Nenhum dado encontrado para o período selecionado.</div>;

  return (
    <div className="channel-performance card">
      <h3>Performance por Canal</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Canal</th>
              <th>Pedidos</th>
              <th>Itens</th>
              <th>Faturação</th>
              <th>Tempo Médio</th>
              <th>Pedidos Atrasados</th>
            </tr>
          </thead>
          <tbody>
            {data.map((channel) => (
              <tr key={channel.channel_name}>
                <td>{channel.channel_name}</td>
                <td>{channel.total_orders}</td>
                <td>{channel.total_items}</td>
                <td>{channel.total_revenue}</td>
                <td>{channel.avg_delivery_time}</td>
                <td>{channel.delayed_orders}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Reports() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  return (
    <div className="reports-container">
      <div className="filters card">
        <h3>Filtros</h3>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
        />
      </div>

      <SalesSummary startDate={startDate} endDate={endDate} />
      <div className="reports-grid">
        <ProductPerformance startDate={startDate} endDate={endDate} />
        <ChannelPerformance startDate={startDate} endDate={endDate} />
      </div>
    </div>
  );
}

export default Reports;