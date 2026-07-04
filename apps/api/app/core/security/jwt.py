"""JWT access-token creation and verification (RS256).

Uses an asymmetric keypair so downstream services (AI engine, gateway) can
verify tokens with the public key without holding the signing secret.

Key resolution order:
1. Inline PEM from settings (jwt_private_key / jwt_public_key).
2. PEM files at configured paths.
3. Development fallback: generate an ephemeral in-memory keypair (NEVER in
   production — startup fails instead).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt

from app.core.config import get_settings


class TokenError(Exception):
    """Raised when a token is invalid, expired, or malformed."""


@lru_cache
def _get_keys() -> tuple[str, str]:
    """Return (private_pem, public_pem), resolving from settings or dev fallback."""
    settings = get_settings()

    if settings.jwt_private_key and settings.jwt_public_key:
        return settings.jwt_private_key, settings.jwt_public_key

    if settings.jwt_private_key_path and settings.jwt_public_key_path:
        priv = Path(settings.jwt_private_key_path)
        pub = Path(settings.jwt_public_key_path)
        if priv.is_file() and pub.is_file():
            return priv.read_text(), pub.read_text()

    if settings.is_production:
        raise RuntimeError(
            "JWT signing keys are not configured. Set JWT_PRIVATE_KEY(_PATH) and "
            "JWT_PUBLIC_KEY(_PATH), or run scripts/generate_keys.sh."
        )

    return _generate_ephemeral_keys()


@lru_cache
def _generate_ephemeral_keys() -> tuple[str, str]:
    """Generate an ephemeral RSA keypair for development/testing."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


def create_access_token(
    subject: str,
    *,
    organization_id: str | None = None,
    role: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed access token for the given subject (user id)."""
    settings = get_settings()
    private_key, _ = _get_keys()
    now = datetime.now(UTC)

    claims: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid.uuid4()),
    }
    if organization_id is not None:
        claims["org"] = organization_id
    if role is not None:
        claims["role"] = role
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, private_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token. Raises TokenError on failure."""
    settings = get_settings()
    _, public_key = _get_keys()
    try:
        payload = jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenError(str(exc)) from exc

    if payload.get("type") != "access":
        raise TokenError("Not an access token")
    return payload
