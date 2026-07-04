"""Integration test: live stream token issuance (gateway provisioning mocked)."""

import pytest
from httpx import AsyncClient
from jose import jwt

import app.services.camera_service as camera_service_module
import app.services.stream_service as stream_service_module
from app.core.config import get_settings
from app.core.rtsp import ProbeResult, ProbeStatus
from tests.conftest import RecordingEmailSender

AUTH = "/api/v1/auth"
ORGS = "/api/v1/organizations"
STORES = "/api/v1/stores"
CAMERAS = "/api/v1/cameras"


@pytest.fixture(autouse=True)
def _stubs(monkeypatch):
    async def fake_probe(url, *, username=None, password=None, timeout=12.0, capture_frame=True):
        return ProbeResult(ProbeStatus.CONNECTED, width=1280, height=720, fps=25.0, codec="h264")

    async def fake_provision(self, path, source):  # noqa: ANN001
        return None

    monkeypatch.setattr(camera_service_module, "probe_rtsp", fake_probe)
    monkeypatch.setattr(stream_service_module.StreamService, "_provision", fake_provision)


async def _camera(client: AsyncClient, recorder: RecordingEmailSender) -> tuple[dict, str]:
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "Owner", "email": "a@example.com", "password": "Sup3r-Secret!"},
    )
    token = recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    store_id = (await client.post(STORES, json={"name": "S"}, headers=headers)).json()["id"]
    cam = (
        await client.post(
            CAMERAS,
            json={"store_id": store_id, "name": "Cam", "rtsp_url": "rtsp://10.0.0.1:554/s"},
            headers=headers,
        )
    ).json()
    return headers, cam["id"]


async def test_start_live_returns_valid_token(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers, camera_id = await _camera(client, email_recorder)

    resp = await client.post(f"{CAMERAS}/{camera_id}/live", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["whep_url"].endswith(f"/whep/{camera_id}")
    assert body["camera_id"] == camera_id

    # The token must verify with the shared secret and carry the camera path.
    claims = jwt.decode(
        body["token"], get_settings().stream_jwt_secret, algorithms=["HS256"]
    )
    assert claims["path"] == camera_id


async def test_start_live_requires_own_camera(
    client: AsyncClient, email_recorder: RecordingEmailSender, db_ready
) -> None:
    headers, camera_id = await _camera(client, email_recorder)

    # A second org cannot start a stream for the first org's camera.
    await client.post(
        f"{AUTH}/register",
        json={"full_name": "B", "email": "b@example.com", "password": "Sup3r-Secret!"},
    )
    token = email_recorder.last_token()
    tokens = (await client.post(f"{AUTH}/verify-email", json={"token": token})).json()["tokens"]
    headers_b = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post(ORGS, json={"name": "Beta"}, headers=headers_b)

    resp = await client.post(f"{CAMERAS}/{camera_id}/live", headers=headers_b)
    assert resp.status_code == 404
