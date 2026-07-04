"""Integration tests: organization settings read/update."""

from httpx import AsyncClient

from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"


async def _onboarded_headers(client: AsyncClient, recorder: RecordingEmailSender) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "Owner", "email": "owner@example.com", "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post(ORGS, json={"name": "Acme", "industry": "retail"}, headers=headers)
    return headers


async def test_get_and_update_settings(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _onboarded_headers(client, email_recorder)

    current = await client.get(f"{ORGS}/current", headers=headers)
    assert current.status_code == 200
    body = current.json()
    assert body["name"] == "Acme"
    assert body["timezone"] == "UTC"
    assert body["currency"] == "USD"
    assert body["alert_email_enabled"] is True
    assert "id" in body and "created_at" in body  # read-only fields present

    updated = await client.patch(
        f"{ORGS}/current",
        json={
            "contact_email": "ops@acme.com",
            "timezone": "Asia/Kolkata",
            "currency": "INR",
            "alert_email_enabled": False,
        },
        headers=headers,
    )
    assert updated.status_code == 200
    result = updated.json()
    assert result["contact_email"] == "ops@acme.com"
    assert result["timezone"] == "Asia/Kolkata"
    assert result["currency"] == "INR"
    assert result["alert_email_enabled"] is False


async def test_settings_require_onboarding(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "New", "email": "new@example.com", "password": "Sup3r-Secret!"},
    )
    token = email_recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(f"{ORGS}/current", headers=headers)
    assert resp.status_code == 409
