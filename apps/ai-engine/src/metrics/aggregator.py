"""Per-camera, per-minute metrics aggregator.

Accumulates occupancy/queue samples and unique tracks into minute buckets, and
flushes completed buckets as aggregates. Pure and unit-testable; produces only
aggregates (never raw detections).
"""

from __future__ import annotations

from dataclasses import dataclass, field


def minute_of(ts: float) -> int:
    return int(ts // 60) * 60


@dataclass
class _Bucket:
    occupancy: list[int] = field(default_factory=list)
    queue: list[int] = field(default_factory=list)
    tracks: set[int] = field(default_factory=set)


def _build(camera_id: str, minute: int, bucket: _Bucket) -> dict:
    occ = bucket.occupancy or [0]
    q = bucket.queue or [0]
    return {
        "camera_id": camera_id,
        "bucket": float(minute),
        "occupancy_avg": round(sum(occ) / len(occ), 2),
        "occupancy_peak": max(occ),
        "footfall": len(bucket.tracks),
        "queue_avg": round(sum(q) / len(q), 2),
        "queue_peak": max(q),
    }


class MetricsAggregator:
    def __init__(self) -> None:
        self._buckets: dict[tuple[str, int], _Bucket] = {}

    def record(
        self,
        camera_id: str,
        person_count: int,
        queue_count: int,
        track_ids: set[int],
        now: float,
    ) -> None:
        bucket = self._buckets.setdefault((camera_id, minute_of(now)), _Bucket())
        bucket.occupancy.append(person_count)
        bucket.queue.append(queue_count)
        bucket.tracks.update(track_ids)

    def flush_due(self, now: float) -> list[dict]:
        """Return + clear aggregates for buckets older than the current minute."""
        current = minute_of(now)
        out: list[dict] = []
        for key in list(self._buckets):
            camera_id, minute = key
            if minute < current:
                out.append(_build(camera_id, minute, self._buckets.pop(key)))
        return out
