"""Unit tests for RS256 JWT creation/verification."""

import pytest

from app.core.security.jwt import (
    TokenError,
    create_access_token,
    decode_access_token,
)


def test_access_token_roundtrip() -> None:
    token = create_access_token("user-123", organization_id="org-1", role="owner")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["org"] == "org-1"
    assert payload["role"] == "owner"
    assert payload["type"] == "access"
    assert "jti" in payload


def test_token_without_org() -> None:
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert "org" not in payload


def test_tampered_token_rejected() -> None:
    token = create_access_token("user-123")
    with pytest.raises(TokenError):
        decode_access_token(token + "tampered")
