"""Runtime configuration. Secrets are environment-only and fail closed."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ALLOWED_ORIGINS = (
    "https://bailongo-pc-1.tail1e5afd.ts.net:8445",
)


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...]
    encryption_key: str | None
    worker_token: str | None


def get_settings() -> Settings:
    raw_origins = os.getenv("GYM_BOOKING_ALLOWED_ORIGINS", "")
    origins = tuple(
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    ) or DEFAULT_ALLOWED_ORIGINS
    return Settings(
        allowed_origins=origins,
        encryption_key=os.getenv("GYM_BOOKING_ENCRYPTION_KEY"),
        worker_token=os.getenv("GYM_BOOKING_WORKER_TOKEN"),
    )
