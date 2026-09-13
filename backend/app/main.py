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
from .store import wodbuster_document


settings = get_settings()
app = FastAPI(title="Gym Booking Hub API", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
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
    snapshot = wodbuster_document(user_id(user)).get()
    data = snapshot.to_dict() if snapshot.exists else None
    return {"connected": bool(data), "usernameHint": data.get("username_hint") if data else None}


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
    })
    return {"connected": True, "usernameHint": f"•••{username[-2:]}"}
