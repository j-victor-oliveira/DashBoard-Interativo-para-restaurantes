import httpx
import os
import pytest

# O URL da API. Dentro do Docker, o 'api' é o nome do serviço.
# Se corrermos localmente, podemos usar 'http://localhost:8000'
API_URL = os.environ.get("API_URL", "http://api:8000")

# Criamos um cliente HTTP que será usado em todos os testes
# O timeout=10 garante que o teste não falha se a API demorar um pouco a responder
client = httpx.Client(base_url=API_URL, timeout=10.0)

def test_api_root():
    """Testa se a API está online e a responder no endpoint /"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo à API de Analytics v4 (com Churn)!"}

def test_kpi_endpoints():
    """Testa se todos os endpoints de KPI respondem com 200 e o formato correto"""
    kpi_endpoints = [
        "/api/kpi/total_revenue",
        "/api/kpi/avg_ticket",
        "/api/kpi/total_sales_count"
    ]
    for endpoint in kpi_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, f"Endpoint {endpoint} falhou"
        data = response.json()
        assert "label" in data
        assert "value" in data
        assert data["value"] is not None
        assert data["value"] != "N/A" # Garante que um valor foi calculado

def test_analytics_endpoint_basic():
    """Testa o endpoint principal de analytics com uma query simples"""
    params = {
        "metric": "total_sales",
        "group_by": "channel"
    }
    response = client.get("/api/analytics", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0 # Esperamos que devolva dados
    assert "group_key" in data["data"][0]
    assert "value" in data["data"][0]

def test_analytics_endpoint_full_filter():
    """
    Testa o endpoint principal respondendo à pergunta da Maria:
    Top produtos (total_sales) no iFood (channel) na Quinta-feira (day_of_week=4) à Noite (time_block=noite)
    """
    params = {
        "metric": "total_sales",
        "group_by": "product",
        "channel": "iFood",
        "day_of_week": 4,
        "time_block": "noite"
    }
    response = client.get("/api/analytics", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list) # A resposta deve ser uma lista

def test_analytics_endpoint_invalid_metric():
    """Testa se a API rejeita uma métrica inválida com um erro 422"""
    params = {
        "metric": "METRICA_MALICIOSA", # Inválido
        "group_by": "product"
    }
    response = client.get("/api/analytics", params=params)
    # O FastAPI devolve 422 (Unprocessable Entity) para erros de validação
    assert response.status_code == 422 

def test_analytics_endpoint_invalid_group_by():
    """Testa se a API rejeita um 'group_by' inválido com um erro 422"""
    params = {
        "metric": "total_sales",
        "group_by": "SQL_INJECTION_AQUI" # Inválido
    }
    response = client.get("/api/analytics", params=params)
    assert response.status_code == 422

def test_churn_endpoint():
    """Testa o endpoint de clientes em risco (churn)"""
    response = client.get("/api/churn-customers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) # Espera-se uma lista (pode estar vazia)
    if len(data) > 0:
        # Se houver dados, verifica a estrutura
        assert "customer_name" in data[0]
        assert "total_sales" in data[0]
        assert "last_purchase_date" in data[0]
