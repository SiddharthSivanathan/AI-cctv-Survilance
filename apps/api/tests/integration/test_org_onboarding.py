"""Integration tests: company creation / onboarding (one org per user)."""

from httpx import AsyncClient

from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"


async def _authed_headers(client: AsyncClient, recorder: RecordingEmailSender) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "Ada", "email": "ada@example.com", "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_create_organization_makes_user_owner(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _authed_headers(client, email_recorder)

    resp = await client.post(
        ORGS, json={"name": "Acme Retail", "industry": "retail"}, headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["organization"]["name"] == "Acme Retail"
    assert body["organization"]["slug"] == "acme-retail"
    assert body["role"] == "owner"
    assert body["needs_onboarding"] is False


async def test_second_organization_rejected(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _authed_headers(client, email_recorder)
    await client.post(ORGS, json={"name": "Acme Retail"}, headers=headers)

    resp = await client.post(ORGS, json={"name": "Second Co"}, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "organization_exists"


async def test_me_reflects_onboarding_state(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _authed_headers(client, email_recorder)

    before = await client.get(f"{AUTH}/me", headers=headers)
    assert before.json()["needs_onboarding"] is True

    await client.post(ORGS, json={"name": "Acme"}, headers=headers)
    after = await client.get(f"{AUTH}/me", headers=headers)
    assert after.json()["needs_onboarding"] is False
    assert after.json()["organization"]["name"] == "Acme"


async def test_unauthenticated_cannot_create_org(client: AsyncClient, db_ready) -> None:
    resp = await client.post(ORGS, json={"name": "NoAuth"})
    assert resp.status_code == 401
