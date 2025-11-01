import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ProductCard({ product }) {
  return (
    <div className="product-card card">
      <h3>{product.name}</h3>
      <div className="product-stats">
        <div className="stat">
          <label>Preço Base:</label>
          <span>{product.price}</span>
        </div>
        <div className="stat">
          <label>Vendas Totais:</label>
          <span>{product.total_sales}</span>
        </div>
        <div className="stat">
          <label>Faturação Total:</label>
          <span>{product.total_revenue}</span>
        </div>
        <div className="stat">
          <label>Preço Médio:</label>
          <span>{product.avg_price}</span>
        </div>
        <div className="stat">
          <label>Clientes Únicos:</label>
          <span>{product.unique_customers}</span>
        </div>
      </div>
    </div>
  );
}

function ProductAnalytics({ productId }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const response = await axios.get(`http://localhost:8000/api/products/${productId}/analytics`);
        setAnalytics(response.data);
      } catch (err) {
        setError('Erro ao carregar análises do produto');
      } finally {
        setLoading(false);
      }
    }
    
    if (productId) {
      fetchAnalytics();
    }
  }, [productId]);

  if (loading) return <div>Carregando análises...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!analytics) return null;

  return (
    <div className="product-analytics card">
      <h3>Análise Detalhada</h3>
      
      <div className="analytics-grid">
        <div className="analytics-section">
          <h4>Performance por Período</h4>
          <table>
            <thead>
              <tr>
                <th>Período</th>
                <th>Vendas</th>
                <th>Faturação</th>
              </tr>
            </thead>
            <tbody>
              {analytics.period_analysis.map((period) => (
                <tr key={period.period}>
                  <td>{period.period}</td>
                  <td>{period.sales_count}</td>
                  <td>{period.total_revenue}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="analytics-section">
          <h4>Performance por Canal</h4>
          <table>
            <thead>
              <tr>
                <th>Canal</th>
                <th>Vendas</th>
                <th>Faturação</th>
              </tr>
            </thead>
            <tbody>
              {analytics.channel_analysis.map((channel) => (
                <tr key={channel.channel_name}>
                  <td>{channel.channel_name}</td>
                  <td>{channel.sales_count}</td>
                  <td>{channel.total_revenue}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Products() {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchProducts() {
      try {
        const response = await axios.get('http://localhost:8000/api/products');
        setProducts(response.data.data);
      } catch (err) {
        console.error('Erro ao carregar produtos:', err);
        setError(
          `Erro ao carregar produtos: ${err.response?.data?.detail || err.message}. ` +
          'Verifique se a API está rodando em http://localhost:8000'
        );
      } finally {
        setLoading(false);
      }
    }

    fetchProducts();
  }, []);

  if (loading) return <div className="card">Carregando produtos...</div>;
  if (error) return <div className="card error-message">{error}</div>;

  return (
    <div className="products-container">
      <div className="products-grid">
        {products.map((product) => (
          <div key={product.id} onClick={() => setSelectedProduct(product.id)}>
            <ProductCard product={product} />
          </div>
        ))}
      </div>

      {selectedProduct && (
        <ProductAnalytics productId={selectedProduct} />
      )}
    </div>
  );
}

export default Products;