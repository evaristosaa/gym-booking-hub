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


def test_wodbuster_connection_never_returns_password(monkeypatch) -> None:
    class Document:
        def set(self, value):
            self.value = value

    document = Document()
    monkeypatch.setattr("app.main.wodbuster_document", lambda uid: document)
    monkeypatch.setattr("app.main.settings", type("Settings", (), {"encryption_key": "tNVmLEIYRFyRpiUv_cpi7gqwNugR7c3upcYbH21vrk8="})())
    monkeypatch.setattr("app.auth.firebase_token_verifier", lambda: lambda token: {"uid": "user-123"})
    response = TestClient(app).put(
        "/v1/connections/wodbuster",
        headers={"Authorization": "Bearer valid-token"},
        json={"username": "sonia@example.test", "password": "secret-value"},
    )
    assert response.status_code == 200
    assert "password" not in response.text
    assert document.value["password_ciphertext"] != "secret-value"


def test_wodbuster_preflight_allows_put_from_pages() -> None:
    response = TestClient(app).options(
        "/v1/connections/wodbuster",
        headers={
            "Origin": "https://evaristosaa.github.io",
            "Access-Control-Request-Method": "PUT",
        },
    )
    assert response.status_code == 200
    assert "PUT" in response.headers["access-control-allow-methods"]
