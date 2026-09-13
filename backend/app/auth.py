"""Firebase ID-token verification at the API boundary."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Header, HTTPException, status


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return token


def firebase_token_verifier() -> Callable[[str], dict[str, object]]:
    """Initialise Firebase lazily; a health probe never needs cloud credentials."""
    try:
        import firebase_admin
        from firebase_admin import auth, credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.ApplicationDefault())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication verification is unavailable",
        ) from exc
    return auth.verify_id_token


def verified_firebase_user(authorization: str | None = Header(default=None)) -> dict[str, object]:
    """FastAPI dependency yielding only a verified Firebase token payload."""
    token = bearer_token(authorization)
    try:
        return firebase_token_verifier()(token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
