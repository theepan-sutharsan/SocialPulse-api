"""Symmetric encryption helpers for OAuth tokens stored at rest.

Uses Fernet (AES-128-CBC + HMAC). The key comes from ``ENCRYPTION_KEY`` when
provided; otherwise it is deterministically derived from ``JWT_SECRET_KEY`` so
local development works without extra setup. Never store plaintext OAuth tokens.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet() -> Fernet:
    configured = current_app.config.get("ENCRYPTION_KEY")
    if configured:
        key = configured.encode() if isinstance(configured, str) else configured
    else:
        secret = current_app.config["JWT_SECRET_KEY"].encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_token(plaintext: str | None) -> str | None:
    """Encrypt a token string; ``None`` passes through unchanged."""
    if not plaintext:
        return None
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str | None) -> str | None:
    """Decrypt a token string; returns ``None`` on missing/invalid input."""
    if not ciphertext:
        return None
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        return None
