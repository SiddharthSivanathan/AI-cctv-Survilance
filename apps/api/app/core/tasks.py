"""Celery client for enqueuing async work (email/notification delivery).

The API only *enqueues* tasks; the worker executes them. This keeps slow work
(SMTP) off the request path.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from celery import Celery

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("tasks")


@lru_cache
def get_celery() -> Celery:
    return Celery("visionops-api", broker=get_settings().celery_broker_url)


def enqueue_emails(jobs: list[dict[str, Any]]) -> None:
    """Enqueue email send tasks (fire-and-forget; never breaks the request)."""
    if not jobs:
        return
    try:
        celery = get_celery()
        for job in jobs:
            celery.send_task("visionops.notifications.send_email", kwargs=job)
    except Exception as exc:  # noqa: BLE001 - broker issues must not break the request
        logger.warning("enqueue_emails_failed", count=len(jobs), error=str(exc))
