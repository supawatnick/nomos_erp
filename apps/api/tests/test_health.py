import os
os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://nomos:change-me-local-only@localhost:5432/nomos')
from fastapi.testclient import TestClient
from app.main import app
def test_health():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
    assert response.headers['X-Request-ID']
