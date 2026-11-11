from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_filters():
    health = client.get('/api/health')
    filters = client.get('/api/filters')
    assert health.status_code == 200
    assert health.json()['rows'] > 0
    assert filters.status_code == 200
    assert filters.json()['countries']


def test_dashboard_endpoints_return_data():
    paths = ['/api/overview', '/api/trends', '/api/products', '/api/countries',
             '/api/segments', '/api/forecast', '/api/anomalies', '/api/documents']
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)


def test_filters_are_applied_consistently():
    params = {'country': 'Germany', 'start': '2010-12-01', 'end': '2011-12-09'}
    overview = client.get('/api/overview', params=params).json()
    products = client.get('/api/products', params=params).json()
    markets = client.get('/api/countries', params=params).json()
    assert overview['rows'] > 0
    assert all(row['country'] == 'Germany' for row in markets)
    assert isinstance(products, list)


def test_ask_and_filtered_csv_export():
    answer = client.post('/api/ask', json={'question': 'Which country has the highest revenue?'})
    export = client.get('/api/export.csv', params={'country': 'Germany'})
    assert answer.status_code == 200
    assert answer.json()['route'] == 'country_performance'
    assert export.status_code == 200
    assert 'text/csv' in export.headers['content-type']
    assert 'InvoiceNo' in export.text
