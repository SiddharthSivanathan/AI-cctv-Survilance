"""Value objects for the rule engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.rules.geometry import Polygon


@dataclass
class Zone:
    id: str
    polygon: Polygon
    zone_type: str = "occupancy"


@dataclass
class Rule:
    id: str
    camera_id: str
    rule_type: str
    zone_id: str | None
    organization_id: str = ""
    store_id: str = ""
    severity: str = "medium"
    cooldown_seconds: int = 300
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class BusinessEvent:
    """A business event emitted by the rule engine (OPEN or RESOLVED).

    Carries organization_id/store_id (resolved from config) so the Event
    Service can persist without a cross-tenant lookup.
    """

    event_key: str  # stable id used to pair open/resolve
    camera_id: str
    organization_id: str
    store_id: str
    rule_id: str
    event_type: str
    status: str  # "open" | "resolved"
    severity: str
    occurred_at: float  # unix seconds
    metadata: dict[str, Any] = field(default_factory=dict)
    # Base64 JPEG of the firing frame (set on OPEN events only).
    snapshot_b64: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_key": self.event_key,
            "camera_id": self.camera_id,
            "organization_id": self.organization_id,
            "store_id": self.store_id,
            "rule_id": self.rule_id,
            "event_type": self.event_type,
            "status": self.status,
            "severity": self.severity,
            "occurred_at": self.occurred_at,
            "metadata": self.metadata,
            "snapshot_b64": self.snapshot_b64,
        }
