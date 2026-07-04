"""Integration tests: store CRUD + cross-tenant isolation."""

from httpx import AsyncClient

from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"
STORES = "/api/v1/stores"


async def _onboarded_headers(
    client: AsyncClient, recorder: RecordingEmailSender, *, email: str, company: str
) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "Owner", "email": email, "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post(ORGS, json={"name": company}, headers=headers)
    return headers


async def test_store_crud(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _onboarded_headers(
        client, email_recorder, email="a@example.com", company="Acme"
    )

    # Create
    created = await client.post(
        STORES,
        json={"name": "Madurai Store", "city": "Madurai", "country": "IN"},
        headers=headers,
    )
    assert created.status_code == 201
    store = created.json()
    assert store["name"] == "Madurai Store"
    store_id = store["id"]

    # List
    listed = await client.get(STORES, headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    # Get
    got = await client.get(f"{STORES}/{store_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["city"] == "Madurai"

    # Update
    patched = await client.patch(
        f"{STORES}/{store_id}", json={"name": "Madurai Flagship"}, headers=headers
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Madurai Flagship"

    # Delete
    deleted = await client.delete(f"{STORES}/{store_id}", headers=headers)
    assert deleted.status_code == 204
    assert (await client.get(STORES, headers=headers)).json() == []


async def test_stores_are_tenant_isolated(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers_a = await _onboarded_headers(
        client, email_recorder, email="a@example.com", company="Acme"
    )
    headers_b = await _onboarded_headers(
        client, email_recorder, email="b@example.com", company="Beta"
    )

    created = await client.post(STORES, json={"name": "A-Store"}, headers=headers_a)
    store_a_id = created.json()["id"]

    # Org B cannot see or fetch org A's store.
    assert (await client.get(STORES, headers=headers_b)).json() == []
    cross = await client.get(f"{STORES}/{store_a_id}", headers=headers_b)
    assert cross.status_code == 404

    # Org B cannot modify or delete it either.
    assert (
        await client.patch(f"{STORES}/{store_a_id}", json={"name": "hijack"}, headers=headers_b)
    ).status_code == 404
    assert (await client.delete(f"{STORES}/{store_a_id}", headers=headers_b)).status_code == 404


async def test_store_requires_onboarding(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    # Verified but no organization yet.
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "New", "email": "new@example.com", "password": "Sup3r-Secret!"},
    )
    token = email_recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(STORES, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "onboarding_required"
