"""Integration tests: Event Service ingest (dedup, open/resolve) + alerts."""

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
        return ProbeResult(ProbeStatus.CONNECTED, width=1280, height=720)

    monkeypatch.setattr(camera_service_module, "probe_rtsp", fake_probe)


async def _setup(client: AsyncClient, recorder: RecordingEmailSender) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "Owner", "email": "a@example.com", "password": "Sup3r-Secret!"},
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
    return {
        "headers": headers,
        "org_id": cam["organization_id"],
        "store_id": store["id"],
        "camera_id": cam["id"],
    }


def _event(ctx: dict, *, status: str, key: str = "cam:r1", etype: str = "queue_threshold_exceeded"):
    return {
        "event_key": key,
        "camera_id": ctx["camera_id"],
        "organization_id": ctx["org_id"],
        "store_id": ctx["store_id"],
        "event_type": etype,
        "status": status,
        "severity": "high",
        "occurred_at": time.time(),
        "metadata": {"count": 6},
    }


async def test_open_creates_event_and_alert(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    resp = await client.post(
        "/api/v1/internal/events", json={"events": [_event(ctx, status="open")]}, headers=INTERNAL
    )
    assert resp.status_code == 200
    assert resp.json()["created"] == 1

    events = await client.get("/api/v1/events", headers=ctx["headers"])
    assert len(events.json()) == 1
    assert events.json()[0]["status"] == "open"

    alerts = await client.get("/api/v1/alerts", headers=ctx["headers"])
    assert len(alerts.json()) == 1


async def test_duplicate_open_is_deduped(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    await client.post(
        "/api/v1/internal/events", json={"events": [_event(ctx, status="open")]}, headers=INTERNAL
    )
    resp = await client.post(
        "/api/v1/internal/events", json={"events": [_event(ctx, status="open")]}, headers=INTERNAL
    )
    assert resp.json()["created"] == 0
    assert resp.json()["deduped"] == 1
    assert len((await client.get("/api/v1/events", headers=ctx["headers"])).json()) == 1


async def test_resolve_closes_event(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    await client.post(
        "/api/v1/internal/events", json={"events": [_event(ctx, status="open")]}, headers=INTERNAL
    )
    resp = await client.post(
        "/api/v1/internal/events",
        json={"events": [_event(ctx, status="resolved", etype="queue_resolved")]},
        headers=INTERNAL,
    )
    assert resp.json()["resolved"] == 1
    resolved = await client.get("/api/v1/events?status=resolved", headers=ctx["headers"])
    assert len(resolved.json()) == 1
    assert resolved.json()[0]["ended_at"] is not None


async def test_events_require_internal_token(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    resp = await client.post("/api/v1/internal/events", json={"events": [_event(ctx, status="open")]})
    assert resp.status_code == 401


async def test_acknowledge_alert(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    await client.post(
        "/api/v1/internal/events", json={"events": [_event(ctx, status="open")]}, headers=INTERNAL
    )
    alert_id = (await client.get("/api/v1/alerts", headers=ctx["headers"])).json()[0]["id"]
    ack = await client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=ctx["headers"])
    assert ack.status_code == 200
    assert ack.json()["acknowledged"] is True
