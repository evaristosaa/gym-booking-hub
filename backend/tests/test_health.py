from fastapi.testclient import TestClient

from app.main import app


def test_health_is_public_and_minimal() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gym-booking-hub-api"}


def test_session_requires_a_bearer_token() -> None:
    response = TestClient(app).get("/v1/session")
    assert response.status_code == 401
