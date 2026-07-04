"""Integration tests: zone + rule CRUD and tenant isolation."""

import pytest
from httpx import AsyncClient

import app.services.camera_service as camera_service_module
from app.core.rtsp import ProbeResult, ProbeStatus
from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"
STORES = "/api/v1/stores"
CAMERAS = "/api/v1/cameras"
ZONES = "/api/v1/zones"
RULES = "/api/v1/rules"

SQUARE = [[0, 0], [100, 0], [100, 100], [0, 100]]


@pytest.fixture(autouse=True)
def _stub_probe(monkeypatch):
    async def fake_probe(url, *, username=None, password=None, timeout=12.0, capture_frame=True):
        return ProbeResult(ProbeStatus.CONNECTED)

    monkeypatch.setattr(camera_service_module, "probe_rtsp", fake_probe)


async def _camera(client: AsyncClient, recorder: RecordingEmailSender, *, email: str) -> tuple[dict, str]:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "O", "email": email, "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post(ORGS, json={"name": "Acme"}, headers=headers)
    store = (await client.post(STORES, json={"name": "S"}, headers=headers)).json()
    cam = (
        await client.post(
            CAMERAS,
            json={"store_id": store["id"], "name": "Cam", "rtsp_url": "rtsp://10.0.0.1:554/s"},
            headers=headers,
        )
    ).json()
    return headers, cam["id"]


async def test_zone_and_rule_crud(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers, camera_id = await _camera(client, email_recorder, email="a@example.com")

    zone = await client.post(
        ZONES,
        json={"camera_id": camera_id, "name": "Checkout", "zone_type": "queue", "polygon": SQUARE},
        headers=headers,
    )
    assert zone.status_code == 201
    zone_id = zone.json()["id"]

    rule = await client.post(
        RULES,
        json={
            "camera_id": camera_id,
            "zone_id": zone_id,
            "name": "Queue > 5",
            "rule_type": "queue_threshold",
            "severity": "high",
            "config": {"threshold": 5},
        },
        headers=headers,
    )
    assert rule.status_code == 201
    rule_id = rule.json()["id"]
    assert rule.json()["rule_type"] == "queue_threshold"

    assert len((await client.get(RULES, headers=headers)).json()) == 1

    patched = await client.patch(f"{RULES}/{rule_id}", json={"enabled": False}, headers=headers)
    assert patched.json()["enabled"] is False

    assert (await client.delete(f"{RULES}/{rule_id}", headers=headers)).status_code == 204


async def test_invalid_rule_type_rejected(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers, camera_id = await _camera(client, email_recorder, email="a@example.com")
    resp = await client.post(
        RULES,
        json={"camera_id": camera_id, "name": "x", "rule_type": "make_coffee"},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_rules_are_tenant_isolated(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers_a, camera_a = await _camera(client, email_recorder, email="a@example.com")
    rule = await client.post(
        RULES,
        json={"camera_id": camera_a, "name": "r", "rule_type": "occupancy_limit", "config": {"threshold": 3}},
        headers=headers_a,
    )
    rule_id = rule.json()["id"]

    headers_b, _ = await _camera(client, email_recorder, email="b@example.com")
    assert (await client.get(RULES, headers=headers_b)).json() == []
    assert (await client.get(f"{RULES}/{rule_id}", headers=headers_b)).status_code == 404
