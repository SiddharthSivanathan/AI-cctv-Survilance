"""Report request/response schemas.

The computed report payload is business-user-focused: header, deterministic
executive summary, KPIs, trends, alert + camera tables, and rule-based
recommendations. Narrative + recommendations are deterministic (facts only).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class QueueStats(BaseModel):
    avg_queue_length: float = 0.0
    peak_queue_length: int = 0
    threshold_exceeded_count: int = 0


class AlertSummary(BaseModel):
    total_alerts: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)


class CameraActivityItem(BaseModel):
    camera_id: uuid.UUID
    camera_name: str
    total_footfall: int = 0
    total_events: int = 0
    avg_occupancy: float = 0.0
    peak_occupancy: int = 0
    uptime_pct: float = 0.0
    status: str = "unknown"


class AlertRow(BaseModel):
    time: datetime
    camera_name: str
    event_type: str
    severity: str
    status: str


class TrendPoint(BaseModel):
    label: str
    value: float


class ReportData(BaseModel):
    """The full computed report payload (stored as JSONB on the Report row)."""

    # Header
    company_name: str
    logo_url: str | None = None
    report_type: str  # daily | weekly | monthly
    start_date: date
    end_date: date
    generated_at: datetime

    # Narrative (deterministic)
    executive_summary: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    # KPIs
    total_footfall: int = 0
    avg_occupancy: float = 0.0
    peak_occupancy: int = 0
    total_alerts: int = 0
    critical_alerts: int = 0
    overall_uptime_pct: float = 0.0
    total_cameras: int = 0
    cameras_online: int = 0
    queue_stats: QueueStats = Field(default_factory=QueueStats)
    alert_summary: AlertSummary = Field(default_factory=AlertSummary)

    # Trends
    footfall_trend: list[TrendPoint] = Field(default_factory=list)
    occupancy_trend: list[TrendPoint] = Field(default_factory=list)
    queue_trend: list[TrendPoint] = Field(default_factory=list)

    # Tables
    alert_rows: list[AlertRow] = Field(default_factory=list)
    cameras: list[CameraActivityItem] = Field(default_factory=list)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_type: str
    period_start: date
    period_end: date
    status: str
    generated_at: datetime
    data: ReportData


class ReportListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_type: str
    period_start: date
    period_end: date
    generated_at: datetime


class GenerateReportRequest(BaseModel):
    report_type: str = "daily"  # daily | weekly | monthly
    end_date: date | None = None  # defaults to today
