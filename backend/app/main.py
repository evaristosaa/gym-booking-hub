"""HTTPS API boundary for Gym Booking Hub.

This initial slice deliberately exposes no credential endpoint until Firebase token
verification and Firestore rules are deployed. A missing encryption key therefore
cannot accidentally downgrade secrets to plain text.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings
from .auth import verified_firebase_user


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
