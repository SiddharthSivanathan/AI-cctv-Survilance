"""Integration tests: in-app notifications created from events."""

import time

import pytest
from httpx import AsyncClient

import app.services.camera_service as camera_service_module
from app.core.config import get_settings
from app.core.rtsp import ProbeResult, ProbeStatus
from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"
STORES = "/api/v1/stores"
CAMERAS = "/api/v1/cameras"
INTERNAL = {"X-Internal-Token": get_settings().internal_api_token}


@pytest.fixture(autouse=True)
def _stub_probe(monkeypatch):
    async def fake_probe(url, *, username=None, password=None, timeout=12.0, capture_frame=True):
        return ProbeResult(ProbeStatus.CONNECTED)

    monkeypatch.setattr(camera_service_module, "probe_rtsp", fake_probe)


async def _setup(client: AsyncClient, recorder: RecordingEmailSender) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "O", "email": "a@example.com", "password": "Sup3r-Secret!"},
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
    return {"headers": headers, "org": cam["organization_id"], "store": store["id"], "cam": cam["id"]}


async def _emit_open(client: AsyncClient, ctx: dict) -> None:
    await client.post(
        "/api/v1/internal/events",
        json={
            "events": [
                {
                    "event_key": "cam:r1",
                    "camera_id": ctx["cam"],
                    "organization_id": ctx["org"],
                    "store_id": ctx["store"],
                    "event_type": "unattended_billing_counter",
                    "status": "open",
                    "severity": "high",
                    "occurred_at": time.time(),
                    "metadata": {"empty_seconds": 120},
                }
            ]
        },
        headers=INTERNAL,
    )


async def test_event_creates_notification(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    await _emit_open(client, ctx)

    resp = await client.get("/api/v1/notifications", headers=ctx["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["unread_count"] == 1
    assert body["items"][0]["event_type"] == "unattended_billing_counter"

    count = await client.get("/api/v1/notifications/unread-count", headers=ctx["headers"])
    assert count.json()["unread"] == 1


async def test_mark_read_and_all(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    await _emit_open(client, ctx)
    notif_id = (await client.get("/api/v1/notifications", headers=ctx["headers"])).json()["items"][0]["id"]

    read = await client.post(f"/api/v1/notifications/{notif_id}/read", headers=ctx["headers"])
    assert read.status_code == 200
    assert read.json()["is_read"] is True

    unread = await client.get("/api/v1/notifications/unread-count", headers=ctx["headers"])
    assert unread.json()["unread"] == 0

    all_read = await client.post("/api/v1/notifications/read-all", headers=ctx["headers"])
    assert all_read.status_code == 200
