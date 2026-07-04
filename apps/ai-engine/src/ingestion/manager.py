"""Sampler manager.

Periodically reconciles the set of running frame samplers with the enabled
cameras reported by the control plane, provisioning MediaMTX paths as needed.
"""

from __future__ import annotations

import threading

import redis
import structlog

from src.config import get_settings
from src.ingestion.api_client import ControlPlaneClient
from src.ingestion.sampler import FrameSampler

logger = structlog.get_logger("sampler.manager")


class SamplerManager:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client
        self._settings = get_settings()
        self._control = ControlPlaneClient()
        self._samplers: dict[str, FrameSampler] = {}
        self._fps: dict[str, int] = {}

    def reconcile(self) -> None:
        streams = self._control.list_camera_streams()
        desired = {s.camera_id: s for s in streams}

        # Start / restart samplers for desired cameras.
        for camera_id, stream in desired.items():
            if camera_id in self._samplers and self._fps.get(camera_id) == stream.sample_fps:
                continue
            if camera_id in self._samplers:  # fps changed -> restart
                self._samplers.pop(camera_id).stop()
            self._control.provision_path(camera_id, stream.source)
            sampler = FrameSampler(camera_id, stream.sample_fps, self._client)
            sampler.start()
            self._samplers[camera_id] = sampler
            self._fps[camera_id] = stream.sample_fps
            logger.info("sampler_started", camera_id=camera_id, fps=stream.sample_fps)

        # Stop samplers for cameras no longer enabled.
        for camera_id in list(self._samplers):
            if camera_id not in desired:
                self._samplers.pop(camera_id).stop()
                self._fps.pop(camera_id, None)
                logger.info("sampler_stopped", camera_id=camera_id)

    def run_forever(self, stop: threading.Event) -> None:
        while not stop.is_set():
            try:
                self.reconcile()
            except Exception as exc:  # noqa: BLE001 - keep manager alive
                logger.warning("reconcile_failed", error=str(exc))
            stop.wait(self._settings.stream_poll_interval_seconds)

    def shutdown(self) -> None:
        for sampler in self._samplers.values():
            sampler.stop()
        self._samplers.clear()
