"""Camera service.

Owns credential encryption, RTSP probing (via ffmpeg), thumbnail capture, and
status updates. Passwords are encrypted on write and only decrypted in-process
to open a connection — never returned or logged.
"""

from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

from app.core.crypto import decrypt, encrypt, strip_userinfo
from app.core.exceptions import NotFoundError, ValidationError
from app.core.rtsp import ProbeResult, ProbeStatus, probe_rtsp
from app.core.storage import ObjectStorage, StorageError
from app.models.camera import Camera
from app.repositories.camera_repository import CameraRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.camera import (
    ConnectionTestResult,
    CreateCameraRequest,
    TestConnectionRequest,
    UpdateCameraRequest,
)
from app.services.audit_service import AuditService


class CameraService:
    def __init__(
        self,
        camera_repo: CameraRepository,
        store_repo: StoreRepository,
        audit_service: AuditService,
        storage: ObjectStorage,
    ) -> None:
        self._cameras = camera_repo
        self._stores = store_repo
        self._audit = audit_service
        self._storage = storage

    # ----- queries ---------------------------------------------------------

    async def list(
        self, organization_id: uuid.UUID, *, store_id: uuid.UUID | None = None
    ) -> list[Camera]:
        return await self._cameras.list_for_org(organization_id, store_id=store_id)

    async def get(self, camera_id: uuid.UUID, organization_id: uuid.UUID) -> Camera:
        camera = await self._cameras.get_for_org(camera_id, organization_id)
        if camera is None:
            raise NotFoundError("Camera not found")
        return camera

    async def _assert_store(self, store_id: uuid.UUID, organization_id: uuid.UUID) -> None:
        if await self._stores.get_for_org(store_id, organization_id) is None:
            raise ValidationError("Store not found in this organization")

    # ----- mutations -------------------------------------------------------

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        data: CreateCameraRequest,
    ) -> Camera:
        await self._assert_store(data.store_id, organization_id)
        camera = Camera(
            organization_id=organization_id,
            store_id=data.store_id,
            name=data.name.strip(),
            camera_type=data.camera_type,
            description=data.description,
            rtsp_url=strip_userinfo(data.rtsp_url),
            username=data.username,
            password_encrypted=encrypt(data.password) if data.password else None,
            manufacturer=data.manufacturer,
            model=data.model,
            sample_fps=data.sample_fps,
        )
        await self._cameras.add(camera)
        # Probe once on create to establish status + metadata + thumbnail.
        await self._probe_and_update(camera)
        await self._audit.record(
            action="camera.created",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            resource_type="camera",
            resource_id=str(camera.id),
            metadata={"name": camera.name, "status": camera.status},
        )
        return camera

    async def update(
        self,
        *,
        camera_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        data: UpdateCameraRequest,
    ) -> Camera:
        camera = await self.get(camera_id, organization_id)
        fields = data.model_dump(exclude_unset=True)

        if "store_id" in fields and fields["store_id"] is not None:
            await self._assert_store(fields["store_id"], organization_id)
            camera.store_id = fields["store_id"]
        for attr in ("name", "description", "sample_fps", "enabled", "username"):
            if attr in fields and fields[attr] is not None:
                setattr(camera, attr, fields[attr])
        if fields.get("rtsp_url"):
            camera.rtsp_url = strip_userinfo(fields["rtsp_url"])
        # Only replace the password when a non-empty value is supplied.
        if fields.get("password"):
            camera.password_encrypted = encrypt(fields["password"])

        await self._cameras.session.flush()
        await self._audit.record(
            action="camera.updated",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            resource_type="camera",
            resource_id=str(camera.id),
        )
        return camera

    async def delete(
        self,
        *,
        camera_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> None:
        camera = await self.get(camera_id, organization_id)
        await self._cameras.delete(camera)
        await self._audit.record(
            action="camera.deleted",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            resource_type="camera",
            resource_id=str(camera_id),
        )

    # ----- connection testing ---------------------------------------------

    async def test(self, camera_id: uuid.UUID, organization_id: uuid.UUID) -> Camera:
        """Re-probe an existing camera and update its status."""
        camera = await self.get(camera_id, organization_id)
        await self._probe_and_update(camera)
        return camera

    async def test_connection(self, data: TestConnectionRequest) -> ConnectionTestResult:
        """Probe an arbitrary RTSP URL (pre-save) and return the result + preview."""
        result = await probe_rtsp(
            data.rtsp_url, username=data.username, password=data.password
        )
        thumbnail_url = None
        if result.frame_jpeg:
            thumbnail_url = self._upload_thumbnail(result.frame_jpeg, prefix="preview")
        return ConnectionTestResult(
            status=result.status.value,
            message=result.message,
            resolution=result.resolution,
            fps=result.fps,
            codec=result.codec,
            thumbnail_url=thumbnail_url,
        )

    async def _probe_and_update(self, camera: Camera) -> ProbeResult:
        password = decrypt(camera.password_encrypted) if camera.password_encrypted else None
        result = await probe_rtsp(camera.rtsp_url, username=camera.username, password=password)

        if result.status is ProbeStatus.CONNECTED:
            camera.status = "online"
            camera.last_seen_at = datetime.now(UTC)
            camera.last_error = None
            camera.offline_alerted_at = None
            camera.resolution = result.resolution or camera.resolution
            camera.fps = result.fps or camera.fps
            camera.codec = result.codec or camera.codec
            if result.frame_jpeg:
                url = self._upload_thumbnail(
                    result.frame_jpeg, prefix=f"cameras/{camera.organization_id}/{camera.id}"
                )
                if url:
                    camera.thumbnail_url = url
        else:
            camera.status = "offline"
            camera.last_error = f"{result.status.value}: {result.message or ''}".strip()

        await self._cameras.session.flush()
        return result

    def _upload_thumbnail(self, frame: bytes, *, prefix: str) -> str | None:
        try:
            return self._storage.upload_public(
                io.BytesIO(frame),
                key=f"{prefix}/thumb-{uuid.uuid4()}.jpg",
                content_type="image/jpeg",
            )
        except StorageError:
            return None
