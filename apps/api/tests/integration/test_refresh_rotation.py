"""Integration tests: refresh-token rotation and reuse detection."""

from httpx import AsyncClient

from tests.conftest import RecordingEmailSender

API = "/api/v1/auth"


async def _verified_tokens(client: AsyncClient, recorder: RecordingEmailSender) -> dict:
    await client.post(
        f"{API}/register",
        json={"full_name": "Ada", "email": "ada@example.com", "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    resp = await client.post(f"{API}/verify-email", json={"token": token})
    return resp.json()["tokens"]


async def test_refresh_rotates_tokens(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    tokens = await _verified_tokens(client, email_recorder)
    resp = await client.post(f"{API}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert new_tokens["access_token"]


async def test_reuse_of_rotated_token_is_rejected(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    tokens = await _verified_tokens(client, email_recorder)
    old_refresh = tokens["refresh_token"]

    first = await client.post(f"{API}/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200

    # Reusing the now-rotated token must fail (reuse detection).
    reuse = await client.post(f"{API}/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401
    assert reuse.json()["error"]["code"] == "invalid_token"

    # And the freshly issued token from the compromised family is also revoked.
    new_refresh = first.json()["refresh_token"]
    after = await client.post(f"{API}/refresh", json={"refresh_token": new_refresh})
    assert after.status_code == 401


async def test_logout_revokes_refresh(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    tokens = await _verified_tokens(client, email_recorder)
    await client.post(f"{API}/logout", json={"refresh_token": tokens["refresh_token"]})
    resp = await client.post(f"{API}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401
