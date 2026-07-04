"""AI engine service entrypoint.

Phase 2: establishes the service lifecycle — configuration, logging, Redis
connectivity, and a graceful run loop. The frame-consumption + detection
pipeline is implemented in Phase 7. No inference logic here yet.
"""

from __future__ import annotations

import signal
import sys
import time
from types import FrameType

import redis
import structlog

from src import __version__
from src.config import get_settings

logger = structlog.get_logger("ai-engine")

_shutdown = False


def _handle_signal(signum: int, _frame: FrameType | None) -> None:
    global _shutdown
    logger.info("shutdown_signal_received", signal=signal.Signals(signum).name)
    _shutdown = True


def check_redis(url: str) -> bool:
    """Return True if Redis is reachable."""
    try:
        client = redis.from_url(url)
        client.ping()
        client.close()
        return True
    except redis.RedisError as exc:
        logger.warning("redis_unavailable", error=str(exc))
        return False


def main() -> int:
    """Run the AI engine service loop."""
    settings = get_settings()
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info(
        "ai_engine_starting",
        version=__version__,
        environment=settings.environment,
        device=settings.ai_device,
    )

    redis_ok = check_redis(settings.redis_url)
    logger.info("ai_engine_ready", redis=redis_ok)

    # Idle heartbeat loop until the pipeline is wired in Phase 7.
    while not _shutdown:
        time.sleep(5)

    logger.info("ai_engine_stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
