"""AI engine service entrypoint.

Runs two cooperating components in one process for V1:
  * SamplerManager — provisions MediaMTX paths and runs ffmpeg frame samplers.
  * DetectionWorker — consumes frames, runs YOLOv11s + tracking, publishes
    detections to Redis.

Both are stateless and database-free. The rule engine (Phase 8) consumes the
detection stream. Components can later be split into separate deployments.
"""

from __future__ import annotations

import signal
import sys
import threading
from types import FrameType

import structlog

from src import __version__
from src.config import get_settings
from src.ingestion.manager import SamplerManager
from src.pipeline.worker import DetectionWorker
from src.redis_streams import get_client

logger = structlog.get_logger("ai-engine")

_stop = threading.Event()


def _handle_signal(signum: int, _frame: FrameType | None) -> None:
    logger.info("shutdown_signal_received", signal=signal.Signals(signum).name)
    _stop.set()


def main() -> int:
    settings = get_settings()
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("ai_engine_starting", version=__version__, device=settings.ai_device)

    client = get_client()
    manager = SamplerManager(client)
    worker = DetectionWorker(client)

    manager_thread = threading.Thread(
        target=manager.run_forever, args=(_stop,), name="sampler-manager", daemon=True
    )
    manager_thread.start()

    logger.info("ai_engine_ready")
    try:
        worker.run_forever(_stop)
    finally:
        _stop.set()
        manager.shutdown()
        logger.info("ai_engine_stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
