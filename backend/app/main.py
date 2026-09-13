"""HTTPS API boundary for Gym Booking Hub.

This initial slice deliberately exposes no credential endpoint until Firebase token
verification and Firestore rules are deployed. A missing encryption key therefore
cannot accidentally downgrade secrets to plain text.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings


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
