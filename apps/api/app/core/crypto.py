"""Symmetric encryption for sensitive credentials (Fernet / AES-128-CBC+HMAC).

Camera RTSP passwords are encrypted at rest and decrypted only in-process to
open a connection. Ciphertext is stored; plaintext never leaves this module's
callers except when actively connecting.
"""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse, urlunparse

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class DecryptionError(Exception):
    """Raised when ciphertext cannot be decrypted (wrong key or corrupt)."""


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().credentials_encryption_key
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str) -> str:
    """Encrypt a string, returning URL-safe ciphertext."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt ciphertext produced by :func:`encrypt`."""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError) as exc:
        raise DecryptionError("Could not decrypt credential") from exc


def strip_userinfo(url: str) -> str:
    """Return an RTSP URL with any embedded user:password removed.

    Used so responses/logs never leak credentials embedded in the URL.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return url
    if "@" in parsed.netloc:
        host = parsed.netloc.rsplit("@", 1)[1]
        parsed = parsed._replace(netloc=host)
    return urlunparse(parsed)
