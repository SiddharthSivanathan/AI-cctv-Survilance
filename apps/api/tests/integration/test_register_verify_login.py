"""Integration tests: registration → email verification → login."""

from httpx import AsyncClient

from tests.conftest import RecordingEmailSender

API = "/api/v1/auth"


async def _register(client: AsyncClient, email: str = "owner@example.com") -> None:
    resp = await client.post(
        f"{API}/register",
        json={"full_name": "Ada Owner", "email": email, "password": "Sup3r-Secret!"},
    )
    assert resp.status_code == 201


async def test_register_creates_account(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    await _register(client)
    assert len(email_recorder.messages) == 1
    assert "verify" in email_recorder.messages[0].subject.lower()


async def test_login_blocked_until_verified(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    await _register(client)
    resp = await client.post(
        f"{API}/login", json={"email": "owner@example.com", "password": "Sup3r-Secret!"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "email_not_verified"


async def test_verify_then_login(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    await _register(client)
    token = email_recorder.last_token()

    verify = await client.post(f"{API}/verify-email", json={"token": token})
    assert verify.status_code == 200
    body = verify.json()
    assert body["tokens"]["access_token"]
    assert body["user"]["needs_onboarding"] is True

    login = await client.post(
        f"{API}/login", json={"email": "owner@example.com", "password": "Sup3r-Secret!"}
    )
    assert login.status_code == 200
    assert login.json()["user"]["user"]["is_email_verified"] is True


async def test_duplicate_email_rejected(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    await _register(client)
    resp = await client.post(
        f"{API}/register",
        json={"full_name": "Copy", "email": "owner@example.com", "password": "Another-1!"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "email_already_exists"


async def test_invalid_verification_token_rejected(client: AsyncClient, db_ready) -> None:
    resp = await client.post(f"{API}/verify-email", json={"token": "bogus"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"
