"""Integration tests: camera CRUD, credential masking, tenant isolation."""

import pytest
from httpx import AsyncClient

import app.services.camera_service as camera_service_module
from app.core.rtsp import ProbeResult, ProbeStatus
from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"
STORES = "/api/v1/stores"
CAMERAS = "/api/v1/cameras"


@pytest.fixture(autouse=True)
def _stub_probe(monkeypatch):
    """Avoid real ffmpeg: probe always reports a connected 1080p stream."""

    async def fake_probe(url, *, username=None, password=None, timeout=12.0, capture_frame=True):
        return ProbeResult(
            ProbeStatus.CONNECTED,
            width=1920,
            height=1080,
            fps=25.0,
            codec="h264",
            frame_jpeg=None,  # no frame => no storage upload in tests
            message="Connected",
        )

    monkeypatch.setattr(camera_service_module, "probe_rtsp", fake_probe)


async def _onboarded(client: AsyncClient, recorder: RecordingEmailSender, *, email: str) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "Owner", "email": email, "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post(ORGS, json={"name": "Acme"}, headers=headers)
    return headers


async def _store(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(STORES, json={"name": "Madurai"}, headers=headers)
    return resp.json()["id"]


async def test_camera_crud_and_credential_masking(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _onboarded(client, email_recorder, email="a@example.com")
    store_id = await _store(client, headers)

    created = await client.post(
        CAMERAS,
        json={
            "store_id": store_id,
            "name": "Billing Counter",
            "rtsp_url": "rtsp://admin:secret@192.168.1.10:554/stream1",
            "username": "admin",
            "password": "secret",
        },
        headers=headers,
    )
    assert created.status_code == 201
    cam = created.json()
    # Credentials must never be returned; URL userinfo stripped.
    assert "password" not in cam or cam.get("password") is None
    assert cam["has_credentials"] is True
    assert cam["username"] == "admin"
    assert cam["rtsp_url"] == "rtsp://192.168.1.10:554/stream1"
    assert cam["status"] == "online"
    assert cam["resolution"] == "1920x1080"
    camera_id = cam["id"]

    # List + get
    assert len((await client.get(CAMERAS, headers=headers)).json()) == 1
    got = await client.get(f"{CAMERAS}/{camera_id}", headers=headers)
    assert got.json()["codec"] == "h264"

    # Update name; omit password keeps credentials.
    patched = await client.patch(
        f"{CAMERAS}/{camera_id}", json={"name": "Counter 1"}, headers=headers
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Counter 1"
    assert patched.json()["has_credentials"] is True

    # Delete
    assert (await client.delete(f"{CAMERAS}/{camera_id}", headers=headers)).status_code == 204


async def test_camera_response_never_contains_password(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _onboarded(client, email_recorder, email="a@example.com")
    store_id = await _store(client, headers)
    created = await client.post(
        CAMERAS,
        json={
            "store_id": store_id,
            "name": "Cam",
            "rtsp_url": "rtsp://10.0.0.5:554/s",
            "password": "topsecret",
        },
        headers=headers,
    )
    assert "topsecret" not in created.text


async def test_cameras_are_tenant_isolated(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers_a = await _onboarded(client, email_recorder, email="a@example.com")
    store_a = await _store(client, headers_a)
    created = await client.post(
        CAMERAS,
        json={"store_id": store_a, "name": "A-Cam", "rtsp_url": "rtsp://10.0.0.1:554/s"},
        headers=headers_a,
    )
    cam_a = created.json()["id"]

    headers_b = await _onboarded(client, email_recorder, email="b@example.com")
    assert (await client.get(CAMERAS, headers=headers_b)).json() == []
    assert (await client.get(f"{CAMERAS}/{cam_a}", headers=headers_b)).status_code == 404


async def test_create_camera_rejects_foreign_store(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers_a = await _onboarded(client, email_recorder, email="a@example.com")
    store_a = await _store(client, headers_a)
    headers_b = await _onboarded(client, email_recorder, email="b@example.com")

    # Org B cannot attach a camera to Org A's store.
    resp = await client.post(
        CAMERAS,
        json={"store_id": store_a, "name": "X", "rtsp_url": "rtsp://10.0.0.9:554/s"},
        headers=headers_b,
    )
    assert resp.status_code == 422


async def test_test_connection_endpoint(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers = await _onboarded(client, email_recorder, email="a@example.com")
    resp = await client.post(
        f"{CAMERAS}/test-connection",
        json={"rtsp_url": "rtsp://10.0.0.5:554/s", "username": "admin", "password": "p"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "connected"
    assert resp.json()["resolution"] == "1920x1080"
