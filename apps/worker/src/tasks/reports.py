"""Scheduled report generation tasks.

Triggers the API's internal report-run endpoint (which does the aggregation +
persistence). Reports are generated on a schedule but not emailed.
"""

from __future__ import annotations

import httpx
import structlog

from src.celery_app import celery_app
from src.config import get_settings

logger = structlog.get_logger("reports")


def _run(report_type: str) -> dict | None:
    settings = get_settings()
    url = f"{settings.api_internal_url.rstrip('/')}/api/v1/internal/reports/run"
    try:
        resp = httpx.post(
            url,
            params={"report_type": report_type},
            headers={"X-Internal-Token": settings.internal_api_token},
            timeout=120.0,
        )
        resp.raise_for_status()
        summary = resp.json()
        logger.info("reports_generated", report_type=report_type, **summary)
        return summary
    except httpx.HTTPError as exc:
        logger.warning("reports_run_failed", report_type=report_type, error=str(exc))
        return None


@celery_app.task(name="visionops.reports.generate_daily")
def generate_daily() -> dict | None:
    return _run("daily")


@celery_app.task(name="visionops.reports.generate_weekly")
def generate_weekly() -> dict | None:
    return _run("weekly")


@celery_app.task(name="visionops.reports.generate_monthly")
def generate_monthly() -> dict | None:
    return _run("monthly")
