"""Small, explicit encryption boundary for third-party booking credentials."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class EncryptionUnavailable(RuntimeError):
    """Raised instead of storing a secret when the runtime key is absent/invalid."""


class CredentialCipher:
    def __init__(self, key: str | None) -> None:
        if not key:
            raise EncryptionUnavailable("GYM_BOOKING_ENCRYPTION_KEY is required")
        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise EncryptionUnavailable("GYM_BOOKING_ENCRYPTION_KEY is invalid") from exc

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise ValueError("Cannot encrypt an empty credential")
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Credential ciphertext is invalid") from exc
