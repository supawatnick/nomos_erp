from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_has_request_id() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]

def test_ready_when_database_connects() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_server_owns_canonical_request_id() -> None:
    supplied = "00000000-0000-0000-0000-000000000000"
    response = client.get("/health", headers={"X-Request-ID": supplied})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != supplied
