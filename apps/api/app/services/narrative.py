"""Deterministic report narrative + recommendations.

Facts-only: every bullet is derived from the aggregated numbers — nothing is
invented or speculated. A pluggable LLM narrator is reserved for V2 behind this
same function signature.
"""

from __future__ import annotations

from app.schemas.report import ReportData


def _pct_change(current: int, previous: int) -> str | None:
    if previous <= 0:
        return None
    change = round((current - previous) / previous * 100)
    if change == 0:
        return "roughly flat vs the previous period"
    direction = "increased" if change > 0 else "decreased"
    return f"{direction} by {abs(change)}% vs the previous period"


def executive_summary(data: ReportData, previous_footfall: int) -> list[str]:
    bullets: list[str] = []

    change = _pct_change(data.total_footfall, previous_footfall)
    if change:
        bullets.append(f"Total footfall was {data.total_footfall}, {change}.")
    else:
        bullets.append(f"Total footfall was {data.total_footfall}.")

    if data.peak_occupancy:
        bullets.append(f"Peak occupancy reached {data.peak_occupancy}.")

    unattended = data.alert_summary.by_type.get("unattended_billing_counter", 0)
    if unattended:
        bullets.append(f"{unattended} unattended billing counter event(s) were detected.")

    if data.alert_summary.total_alerts == 0:
        bullets.append("No alerts were triggered during the period.")
    else:
        bullets.append(
            f"{data.alert_summary.total_alerts} alerts total, "
            f"{data.critical_alerts} critical."
        )

    bullets.append(f"Camera uptime was {data.overall_uptime_pct}%.")
    return bullets


def recommendations(data: ReportData) -> list[str]:
    recs: list[str] = []

    if data.queue_stats.threshold_exceeded_count >= 3:
        recs.append(
            "Queue thresholds were exceeded repeatedly — consider adding a cashier during peak hours."
        )

    if data.alert_summary.by_type.get("unattended_billing_counter", 0) >= 2:
        recs.append(
            "Billing counters were unattended multiple times — review staffing schedules."
        )

    offline_cameras = [c for c in data.cameras if c.uptime_pct < 90]
    for cam in offline_cameras[:3]:
        recs.append(
            f"{cam.camera_name} had low uptime ({cam.uptime_pct}%) — inspect network connectivity."
        )

    if not recs:
        recs.append("Operations remained within acceptable limits throughout the period.")
    return recs
