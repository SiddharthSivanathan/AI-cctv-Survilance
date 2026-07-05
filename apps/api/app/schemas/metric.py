"""Metric ingest schemas (internal)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class IngestMetricItem(BaseModel):
    organization_id: uuid.UUID
    store_id: uuid.UUID | None = None
    camera_id: uuid.UUID
    bucket: float  # unix seconds (minute-truncated by the producer)
    occupancy_avg: float = 0.0
    occupancy_peak: int = 0
    footfall: int = 0
    queue_avg: float = 0.0
    queue_peak: int = 0


class IngestMetricsRequest(BaseModel):
    metrics: list[IngestMetricItem] = Field(default_factory=list)
