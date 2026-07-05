"""Celery application factory.

Phase 2: establishes the broker/result-backend wiring and task discovery.
Rule evaluation, notification fanout, and report generation tasks are added
in their respective phases (8, 10).
"""

from celery import Celery
from celery.schedules import crontab

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "visionops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.tasks",
        "src.tasks.camera_health",
        "src.tasks.notifications",
        "src.tasks.reports",
    ],
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

# Periodic tasks.
celery_app.conf.beat_schedule = {
    "camera-health-sweep": {
        "task": "visionops.cameras.health_sweep",
        "schedule": float(settings.camera_health_interval_seconds),
    },
    # Scheduled report generation (not emailed).
    "daily-report": {
        "task": "visionops.reports.generate_daily",
        "schedule": crontab(hour=0, minute=15),
    },
    "weekly-report": {
        "task": "visionops.reports.generate_weekly",
        "schedule": crontab(hour=0, minute=30, day_of_week=1),
    },
    "monthly-report": {
        "task": "visionops.reports.generate_monthly",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),
    },
}
