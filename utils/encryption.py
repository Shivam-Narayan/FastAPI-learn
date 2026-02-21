from __future__ import annotations

"""
backend/utils/encryption.py

Credential encryption utilities using Fernet symmetric encryption.
"""

from cryptography.fernet import Fernet
import json
import os
from typing import Dict, Any


class CredentialEncryption:
    """Handles encryption/decryption of connection credentials and tokens."""

    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        self.cipher = Fernet(key.encode())

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        json_bytes = json.dumps(credentials).encode()
        encrypted_bytes = self.cipher.encrypt(json_bytes)
        return encrypted_bytes.decode()

    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, Any]:
        encrypted_bytes = encrypted_str.encode()
        decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
        return json.loads(decrypted_bytes.decode())


# singleton
_encryptor: CredentialEncryption | None = None


def get_encryptor() -> CredentialEncryption:
    global _encryptor
    if _encryptor is None:
        _encryptor = CredentialEncryption()
    return _encryptor


# Convenience helpers integrating with Connection model (if available)
try:
    from backend.models.connection import Connection
except ImportError:
    Connection = None  # avoid circular import during model definition


def create_connection_with_creds(credentials: dict, token: dict = None):
    """Helper to create a Connection instance with encrypted fields."""
    encryptor = get_encryptor()
    conn_kwargs = {
        "name": "",
        "provider_key": "",
        "auth_schema_key": "",
        "encrypted_credentials": encryptor.encrypt_credentials(credentials),
    }
    if token:
        conn_kwargs["encrypted_token"] = encryptor.encrypt_credentials(token)
    return Connection(**conn_kwargs)


def get_connection_credentials(connection):
    encryptor = get_encryptor()
    return encryptor.decrypt_credentials(connection.encrypted_credentials)


def get_connection_token(connection):
    if not connection.encrypted_token:
        return None
    encryptor = get_encryptor()
    return encryptor.decrypt_credentials(connection.encrypted_token)
