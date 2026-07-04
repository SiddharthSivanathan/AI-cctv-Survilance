"""Unit tests for Argon2id password hashing."""

from app.core.security.password import hash_password, needs_rehash, verify_password


def test_hash_and_verify_roundtrip() -> None:
    hashed = hash_password("Sup3r-Secret!")
    assert hashed != "Sup3r-Secret!"
    assert verify_password("Sup3r-Secret!", hashed) is True


def test_wrong_password_fails() -> None:
    hashed = hash_password("correct-horse")
    assert verify_password("wrong-horse", hashed) is False


def test_malformed_hash_returns_false() -> None:
    assert verify_password("anything", "not-a-real-hash") is False


def test_needs_rehash_false_for_fresh_hash() -> None:
    assert needs_rehash(hash_password("abc12345")) is False
