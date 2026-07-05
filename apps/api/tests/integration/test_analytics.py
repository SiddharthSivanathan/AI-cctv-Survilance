"""Integration tests: analytics endpoints over aggregated metrics + events."""

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


async def test_overview_and_health(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)

    metric = {
        "organization_id": ctx["org"],
        "store_id": ctx["store"],
        "camera_id": ctx["cam"],
        "bucket": time.time(),
        "occupancy_avg": 4.0,
        "occupancy_peak": 7,
        "footfall": 12,
        "queue_avg": 2.0,
        "queue_peak": 3,
    }
    ingest = await client.post("/api/v1/internal/metrics", json={"metrics": [metric]}, headers=INTERNAL)
    assert ingest.status_code == 200
    assert ingest.json()["written"] == 1

    overview = (await client.get("/api/v1/analytics/overview", headers=ctx["headers"])).json()
    assert overview["active_cameras"] == 1
    assert overview["cameras_online"] == 1
    assert overview["current_occupancy"] == 7
    assert overview["todays_footfall"] == 12

    health = (await client.get("/api/v1/analytics/camera-health", headers=ctx["headers"])).json()
    assert health["total"] == 1
    assert health["online"] == 1
    assert health["uptime_pct"] == 100.0


async def test_timeseries_returns_points(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    await client.post(
        "/api/v1/internal/metrics",
        json={
            "metrics": [
                {
                    "organization_id": ctx["org"],
                    "store_id": ctx["store"],
                    "camera_id": ctx["cam"],
                    "bucket": time.time(),
                    "occupancy_avg": 3.0,
                    "occupancy_peak": 5,
                    "footfall": 8,
                    "queue_avg": 1.0,
                    "queue_peak": 2,
                }
            ]
        },
        headers=INTERNAL,
    )
    ts = (
        await client.get("/api/v1/analytics/timeseries?range=today&bucket=hour", headers=ctx["headers"])
    ).json()
    assert len(ts["points"]) >= 1
    assert ts["points"][0]["footfall"] == 8


async def test_metrics_require_internal_token(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    resp = await client.post("/api/v1/internal/metrics", json={"metrics": []})
    assert resp.status_code == 401
