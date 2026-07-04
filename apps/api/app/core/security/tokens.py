"""Opaque token generation and hashing (refresh, email verification, reset).

Opaque high-entropy tokens are returned to the client in plaintext exactly
once; only their SHA-256 hash is persisted. This means a database leak does
not expose usable tokens.
"""

import hashlib
import secrets


def generate_token() -> str:
    """Generate a URL-safe, high-entropy opaque token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a token for storage/lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token_pair() -> tuple[str, str]:
    """Return (raw_token, token_hash). Store the hash, return the raw once."""
    raw = generate_token()
    return raw, hash_token(raw)
