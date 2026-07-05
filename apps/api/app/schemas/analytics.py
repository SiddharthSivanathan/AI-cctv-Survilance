"""Analytics response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    active_cameras: int
    cameras_online: int
    alerts_today: int
    critical_alerts_today: int
    current_occupancy: int
    todays_footfall: int


class MetricPoint(BaseModel):
    bucket: datetime
    occupancy_avg: float
    occupancy_peak: int
    footfall: int
    queue_avg: float
    queue_peak: int


class TimeseriesResponse(BaseModel):
    points: list[MetricPoint]


class AlertBreakdownResponse(BaseModel):
    by_severity: dict[str, int]
    by_type: dict[str, int]


class CameraHealthResponse(BaseModel):
    total: int
    online: int
    offline: int
    uptime_pct: float
