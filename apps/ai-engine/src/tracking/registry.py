"""Per-camera track lifecycle registry.

Observes track-id-annotated detections each frame and maintains, for every
tracked object: object class, best confidence seen, entry timestamp, last-seen
timestamp, and (on exit) total duration. Purely in-memory and DB-free — the
worker logs a ``track_ended`` summary when a track disappears; persistence
(timeline) is a later phase and does not change this component's interface.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.detection.types import Detection


@dataclass
class TrackInfo:
    track_id: int
    class_name: str
    entry_ts: float
    last_seen_ts: float
    best_confidence: float

    @property
    def duration(self) -> float:
        return max(0.0, self.last_seen_ts - self.entry_ts)


class TrackRegistry:
    """Maintains track lifecycle for a single camera stream."""

    def __init__(self, max_idle_seconds: float = 3.0) -> None:
        self._tracks: dict[int, TrackInfo] = {}
        self._max_idle = max_idle_seconds

    def observe(self, detections: list[Detection], now: float) -> None:
        """Record/refresh every tracked detection seen this frame."""
        for det in detections:
            if det.track_id is None:
                continue
            info = self._tracks.get(det.track_id)
            if info is None:
                self._tracks[det.track_id] = TrackInfo(
                    track_id=det.track_id,
                    class_name=det.class_name,
                    entry_ts=now,
                    last_seen_ts=now,
                    best_confidence=det.confidence,
                )
            else:
                info.last_seen_ts = now
                info.best_confidence = max(info.best_confidence, det.confidence)

    def duration_for(self, track_id: int | None, now: float) -> float | None:
        """Seconds since a track first appeared (for live display)."""
        if track_id is None:
            return None
        info = self._tracks.get(track_id)
        return round(now - info.entry_ts, 2) if info else None

    def sweep_ended(self, now: float) -> list[TrackInfo]:
        """Return and remove tracks not seen within ``max_idle_seconds``."""
        ended = [i for i in self._tracks.values() if now - i.last_seen_ts > self._max_idle]
        for info in ended:
            del self._tracks[info.track_id]
        return ended

    @property
    def active_count(self) -> int:
        return len(self._tracks)
