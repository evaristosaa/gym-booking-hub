import pytest
from cryptography.fernet import Fernet

from app.security import CredentialCipher, EncryptionUnavailable


def test_cipher_round_trip() -> None:
    cipher = CredentialCipher(Fernet.generate_key().decode())
    encrypted = cipher.encrypt("not-a-real-password")
    assert encrypted != "not-a-real-password"
    assert cipher.decrypt(encrypted) == "not-a-real-password"


def test_cipher_fails_closed_without_key() -> None:
    with pytest.raises(EncryptionUnavailable):
        CredentialCipher(None)
