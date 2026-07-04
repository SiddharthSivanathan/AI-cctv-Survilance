"""Unit tests for credential encryption + URL masking."""

import pytest

from app.core.crypto import DecryptionError, decrypt, encrypt, strip_userinfo


def test_encrypt_decrypt_roundtrip() -> None:
    secret = "sup3r-rtsp-p@ss"
    ciphertext = encrypt(secret)
    assert ciphertext != secret
    assert decrypt(ciphertext) == secret


def test_decrypt_rejects_garbage() -> None:
    with pytest.raises(DecryptionError):
        decrypt("not-valid-ciphertext")


def test_strip_userinfo_removes_credentials() -> None:
    assert (
        strip_userinfo("rtsp://admin:secret@192.168.1.10:554/stream1")
        == "rtsp://192.168.1.10:554/stream1"
    )


def test_strip_userinfo_noop_without_credentials() -> None:
    url = "rtsp://192.168.1.10:554/stream1"
    assert strip_userinfo(url) == url
