from fastapi.testclient import TestClient

from backend.main import app


def test_health_contract_remains_stable() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
