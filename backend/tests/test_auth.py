from fastapi.testclient import TestClient

from app.main import app


def test_session_accepts_only_verified_firebase_identity(monkeypatch) -> None:
    monkeypatch.setattr("app.auth.firebase_token_verifier", lambda: lambda token: {"uid": "user-123"})
    response = TestClient(app).get("/v1/session", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 200
    assert response.json() == {"uid": "user-123"}


def test_session_rejects_invalid_token(monkeypatch) -> None:
    def reject():
        def verify(_: str):
            raise RuntimeError("bad token")
        return verify

    monkeypatch.setattr("app.auth.firebase_token_verifier", reject)
    response = TestClient(app).get("/v1/session", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
