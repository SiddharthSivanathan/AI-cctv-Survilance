"""Internal service-to-service endpoints (not tenant-scoped).

Guarded by a shared internal token. Used by the Celery Beat worker (camera
health sweep) and the AI engine (camera stream list for the frame sampler).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionError, decrypt
from app.core.deps import require_internal_token
from app.core.pubsub import publish_many
from app.core.rtsp import build_authenticated_url
from app.core.tasks import enqueue_emails
from app.db.session import get_db, set_org_context
from app.repositories.camera_repository import CameraRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.rule_repository import RuleRepository, ZoneRepository
from app.schemas.event import IngestEventsRequest
from app.schemas.metric import IngestMetricsRequest
from app.services import CameraHealthService, EventService, MetricsService, ReportService

router = APIRouter(
    prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_token)]
)


@router.post("/cameras/health-sweep")
async def camera_health_sweep(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Probe all enabled cameras across all organizations; update + broadcast."""
    service = CameraHealthService(db)
    summary = await service.sweep()
    await db.commit()
    await publish_many(service.messages)
    return summary


@router.get("/cameras/streams")
async def camera_streams(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """Return enabled cameras with decrypted RTSP sources for the AI sampler.

    Internal only. Iterates organizations, setting the RLS context per org so
    cameras are read within their tenant boundary.
    """
    streams: list[dict[str, Any]] = []
    orgs = await OrganizationRepository(db).list_all()
    for org in orgs:
        await set_org_context(db, str(org.id))
        cameras = await CameraRepository(db).list_enabled_for_org(org.id)
        for camera in cameras:
            password = None
            if camera.password_encrypted:
                try:
                    password = decrypt(camera.password_encrypted)
                except DecryptionError:
                    password = None
            streams.append(
                {
                    "camera_id": str(camera.id),
                    "source": build_authenticated_url(camera.rtsp_url, camera.username, password),
                    "sample_fps": camera.sample_fps,
                }
            )
    await set_org_context(db, None)
    return streams


@router.get("/rules-config")
async def rules_config(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """Return per-camera rules + zones for the rule engine (internal)."""
    config: list[dict[str, Any]] = []
    orgs = await OrganizationRepository(db).list_all()
    for org in orgs:
        await set_org_context(db, str(org.id))
        cameras = await CameraRepository(db).list_enabled_for_org(org.id)
        rule_repo, zone_repo = RuleRepository(db), ZoneRepository(db)
        for camera in cameras:
            rules = await rule_repo.list_for_org(org.id, camera_id=camera.id)
            zones = await zone_repo.list_for_camera(org.id, camera.id)
            config.append(
                {
                    "camera_id": str(camera.id),
                    "organization_id": str(org.id),
                    "store_id": str(camera.store_id),
                    "zones": [
                        {"id": str(z.id), "zone_type": z.zone_type, "polygon": z.polygon}
                        for z in zones
                    ],
                    "rules": [
                        {
                            "id": str(r.id),
                            "rule_type": r.rule_type,
                            "zone_id": str(r.zone_id) if r.zone_id else None,
                            "severity": r.severity,
                            "cooldown_seconds": r.cooldown_seconds,
                            "enabled": r.enabled,
                            "config": r.config or {},
                        }
                        for r in rules
                    ],
                }
            )
    await set_org_context(db, None)
    return config


@router.post("/events")
async def ingest_events(
    payload: IngestEventsRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Ingest business events (dedup + open/resolve + alerts), then broadcast.

    Persists first and commits, so real-time subscribers only receive committed
    events (per the Event Service contract).
    """
    summary, messages, email_jobs = await EventService(db).ingest(payload.events)
    await db.commit()
    # Broadcast + enqueue email only after the transaction commits.
    await publish_many(messages)
    enqueue_emails(email_jobs)
    return summary


@router.post("/metrics")
async def ingest_metrics(
    payload: IngestMetricsRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Ingest aggregated per-minute camera metrics from the AI worker."""
    written = await MetricsService(db).ingest(payload.metrics)
    return {"written": written}


@router.post("/reports/run")
async def run_scheduled_reports(
    report_type: str = "daily", db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Generate reports of the given type for every organization (Beat-driven)."""
    orgs = await OrganizationRepository(db).list_all()
    service = ReportService(db)
    generated = 0
    for org in orgs:
        await set_org_context(db, str(org.id))
        await service.generate(org.id, report_type=report_type)
        generated += 1
    await set_org_context(db, None)
    await db.commit()
    return {"generated": generated}
