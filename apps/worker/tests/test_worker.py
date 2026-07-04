"""Smoke tests for the Celery worker skeleton (no broker required)."""

from src.celery_app import celery_app
from src.tasks import ping


def test_celery_app_configured() -> None:
    assert celery_app.main == "visionops"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.timezone == "UTC"


def test_ping_task_runs_directly() -> None:
    # Call the task body directly (no broker) to verify logic.
    assert ping.run() == "pong"


def test_ping_task_registered() -> None:
    assert "visionops.ping" in celery_app.tasks
