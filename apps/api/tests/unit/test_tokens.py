"""Unit tests for opaque token generation/hashing."""

from app.core.security.tokens import generate_token, generate_token_pair, hash_token


def test_generate_token_is_high_entropy_and_unique() -> None:
    a, b = generate_token(), generate_token()
    assert a != b
    assert len(a) >= 40


def test_hash_is_deterministic_and_hex64() -> None:
    token = "some-token"
    assert hash_token(token) == hash_token(token)
    assert len(hash_token(token)) == 64


def test_token_pair_hash_matches() -> None:
    raw, hashed = generate_token_pair()
    assert hash_token(raw) == hashed
