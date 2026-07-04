"""Integration test: camera health sweep + offline event emission."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

import app.services.camera_health_service as health_module
from app.core.rtsp import ProbeResult, ProbeStatus
from app.db.session import AsyncSessionLocal, set_org_context
from app.models.audit_log import AuditLog
from app.models.camera import Camera
from app.models.organization import Organization
from app.models.store import Store
from app.services.camera_health_service import CameraHealthService


async def _seed_offline_camera() -> tuple[uuid.UUID, uuid.UUID]:
    org_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(Organization(id=org_id, name="Acme", slug=f"acme-{org_id.hex[:6]}"))
        await session.flush()
        await set_org_context(session, str(org_id))
        store = Store(organization_id=org_id, name="Store")
        session.add(store)
        await session.flush()
        camera = Camera(
            organization_id=org_id,
            store_id=store.id,
            name="Cam",
            rtsp_url="rtsp://10.0.0.1:554/s",
            status="online",
            last_seen_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        session.add(camera)
        await session.commit()
        return org_id, camera.id


async def test_health_sweep_marks_offline_and_emits_event(monkeypatch, db_ready) -> None:
    org_id, camera_id = await _seed_offline_camera()

    async def fake_probe(url, *, username=None, password=None, timeout=12.0, capture_frame=True):
        return ProbeResult(ProbeStatus.UNREACHABLE, message="Connection refused")

    monkeypatch.setattr(health_module, "probe_rtsp", fake_probe)

    async with AsyncSessionLocal() as session:
        summary = await CameraHealthService(session).sweep()
        await session.commit()

    assert summary["offline"] >= 1
    assert summary["offline_alerts"] >= 1

    async with AsyncSessionLocal() as session:
        await set_org_context(session, str(org_id))
        camera = await session.get(Camera, camera_id)
        assert camera is not None
        assert camera.status == "offline"
        assert camera.offline_alerted_at is not None

        events = (
            (
                await session.execute(
                    select(AuditLog).where(AuditLog.action == "camera.offline")
                )
            )
            .scalars()
            .all()
        )
        assert len(events) == 1


async def test_health_sweep_marks_online(monkeypatch, db_ready) -> None:
    org_id, camera_id = await _seed_offline_camera()

    async def fake_probe(url, *, username=None, password=None, timeout=12.0, capture_frame=True):
        return ProbeResult(ProbeStatus.CONNECTED, message="Connected")

    monkeypatch.setattr(health_module, "probe_rtsp", fake_probe)

    async with AsyncSessionLocal() as session:
        await CameraHealthService(session).sweep()
        await session.commit()

    async with AsyncSessionLocal() as session:
        await set_org_context(session, str(org_id))
        camera = await session.get(Camera, camera_id)
        assert camera is not None
        assert camera.status == "online"
        assert camera.offline_alerted_at is None
