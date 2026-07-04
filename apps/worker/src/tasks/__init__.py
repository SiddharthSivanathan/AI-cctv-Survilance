"""Celery tasks.

A single `ping` task is provided as a liveness/wiring check. Domain tasks
(rules, notifications, reports) are added in later phases.
"""

from src.celery_app import celery_app


@celery_app.task(name="visionops.ping")
def ping() -> str:
    """Trivial task used to verify the broker/worker wiring end-to-end."""
    return "pong"
