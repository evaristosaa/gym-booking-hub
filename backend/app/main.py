"""HTTPS API boundary for Gym Booking Hub.

This initial slice deliberately exposes no credential endpoint until Firebase token
verification and Firestore rules are deployed. A missing encryption key therefore
cannot accidentally downgrade secrets to plain text.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .settings import get_settings
from .auth import verified_firebase_user
from .security import CredentialCipher, EncryptionUnavailable
from .store import wodbuster_connection as load_wodbuster_connection, wodbuster_document
from .wodbuster import InvalidCredentials, WodBusterClient, WodBusterError


settings = get_settings()
app = FastAPI(title="Gym Booking Hub API", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gym-booking-hub-api"}


@app.get("/v1/session", include_in_schema=False)
def session(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, str]:
    """Minimal authenticated endpoint; never returns credentials or claims wholesale."""
    subject = user.get("uid") or user.get("sub")
    if not isinstance(subject, str):
        raise ValueError("Firebase token is missing a subject")
    return {"uid": subject}


class WodBusterConnectionInput(BaseModel):
    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=512)


def user_id(user: dict[str, object]) -> str:
    subject = user.get("uid") or user.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firebase token is missing a subject")
    return subject


@app.get("/v1/connections/wodbuster", include_in_schema=False)
def wodbuster_connection(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    data = wodbuster_connection_data(user_id(user))
    return {
        "configured": bool(data),
        "verified": bool(data and data.get("verified_at")),
        "usernameHint": data.get("username_hint") if data else None,
    }


@app.put("/v1/connections/wodbuster", include_in_schema=False)
def save_wodbuster_connection(
    connection: WodBusterConnectionInput,
    user: dict[str, object] = Depends(verified_firebase_user),
) -> dict[str, object]:
    try:
        cipher = CredentialCipher(settings.encryption_key)
    except EncryptionUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Credential vault unavailable") from exc
    username = connection.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username is required")
    wodbuster_document(user_id(user)).set({
        "username_ciphertext": cipher.encrypt(username),
        "password_ciphertext": cipher.encrypt(connection.password),
        "username_hint": f"•••{username[-2:]}",
        "updated_at": datetime.now(timezone.utc),
        "verified_at": None,
    })
    return {"configured": True, "verified": False, "usernameHint": f"•••{username[-2:]}"}


def wodbuster_connection_data(uid: str) -> dict[str, object] | None:
    return load_wodbuster_connection(uid)


def wodbuster_client(uid: str) -> tuple[WodBusterClient, dict[str, object]]:
    data = wodbuster_connection_data(uid)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WodBuster is not configured")
    try:
        cipher = CredentialCipher(settings.encryption_key)
        username = cipher.decrypt(str(data["username_ciphertext"]))
        password = cipher.decrypt(str(data["password_ciphertext"]))
    except (EncryptionUnavailable, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Credential vault unavailable") from exc
    return WodBusterClient(username, password), data


@app.post("/v1/connections/wodbuster/test", include_in_schema=False)
def test_wodbuster_connection(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    uid = user_id(user)
    client, data = wodbuster_client(uid)
    try:
        box_url = client.box_url()
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Usuario o contraseña de WodBuster incorrectos") from exc
    except WodBusterError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="WodBuster no respondió correctamente") from exc
    wodbuster_document(uid).set({"verified_at": datetime.now(timezone.utc), "box_url_ciphertext": CredentialCipher(settings.encryption_key).encrypt(box_url)}, merge=True)
    return {"verified": True, "usernameHint": data.get("username_hint")}


@app.get("/v1/reservations", include_in_schema=False)
def future_reservations(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    uid = user_id(user)
    client, data = wodbuster_client(uid)
    try:
        cipher = CredentialCipher(settings.encryption_key)
        box_url = cipher.decrypt(str(data["box_url_ciphertext"])) if data.get("box_url_ciphertext") else client.box_url()
        reservations = client.future_confirmed_reservations(box_url)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La sesión WodBuster ya no es válida") from exc
    except WodBusterError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudieron leer las reservas de WodBuster") from exc
    return {"reservations": reservations}
