"""Per-camera in-memory rule state.

Ephemeral: reconstructed from live detections, reset on worker restart, never
persisted. (Redis-backed state is a V2 option for HA.)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CameraState:
    # event_key -> opened_at (unix seconds) for currently-open events
    open_events: dict[str, float] = field(default_factory=dict)
    # event_key -> timestamp until which re-opening is suppressed (post-resolve cooldown)
    cooldown_until: dict[str, float] = field(default_factory=dict)
    # (rule_id, track_id) -> timestamp the track entered the zone (loitering)
    loiter_entered: dict[tuple[str, int], float] = field(default_factory=dict)
    # rule_id -> timestamp the zone became empty (unattended counter)
    absence_since: dict[str, float] = field(default_factory=dict)
    # (rule_id, track_id) -> last side of the line (+1/-1) for line-crossing
    line_side: dict[tuple[str, int], int] = field(default_factory=dict)
