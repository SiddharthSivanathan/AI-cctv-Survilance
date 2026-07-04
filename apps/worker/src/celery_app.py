"""Celery application factory.

Phase 2: establishes the broker/result-backend wiring and task discovery.
Rule evaluation, notification fanout, and report generation tasks are added
in their respective phases (8, 10).
"""

from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "visionops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Beat schedule is populated when scheduled reports land (Phase 10).
celery_app.conf.beat_schedule = {}
