"""Integration tests: report generation + retrieval."""

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
REPORTS = "/api/v1/reports"
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
    # Seed a metric so the report has data.
    await client.post(
        "/api/v1/internal/metrics",
        json={
            "metrics": [
                {
                    "organization_id": cam["organization_id"],
                    "store_id": store["id"],
                    "camera_id": cam["id"],
                    "bucket": time.time(),
                    "occupancy_avg": 3.0,
                    "occupancy_peak": 6,
                    "footfall": 10,
                    "queue_avg": 1.0,
                    "queue_peak": 2,
                }
            ]
        },
        headers=INTERNAL,
    )
    return {"headers": headers, "cam": cam["id"]}


async def test_generate_and_get_report(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)

    gen = await client.post(REPORTS + "/generate", json={"report_type": "daily"}, headers=ctx["headers"])
    assert gen.status_code == 201
    body = gen.json()
    assert body["report_type"] == "daily"
    data = body["data"]
    assert data["total_footfall"] == 10
    assert data["peak_occupancy"] == 6
    assert len(data["executive_summary"]) > 0
    assert len(data["recommendations"]) > 0
    report_id = body["id"]

    listed = await client.get(REPORTS, headers=ctx["headers"])
    assert len(listed.json()) == 1

    fetched = await client.get(f"{REPORTS}/{report_id}", headers=ctx["headers"])
    assert fetched.status_code == 200
    assert fetched.json()["data"]["total_footfall"] == 10


async def test_csv_export(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    report_id = (
        await client.post(REPORTS + "/generate", json={"report_type": "daily"}, headers=ctx["headers"])
    ).json()["id"]
    csv = await client.get(f"{REPORTS}/{report_id}/csv", headers=ctx["headers"])
    assert csv.status_code == 200
    assert "Total footfall" in csv.text


async def test_invalid_report_type(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    ctx = await _setup(client, email_recorder)
    resp = await client.post(REPORTS + "/generate", json={"report_type": "yearly"}, headers=ctx["headers"])
    assert resp.status_code == 422
