"""Multi-object tracking.

V1 ships a deterministic IOU tracker (pure Python, unit-testable) behind a
simple interface. ByteTrack (via `supervision`) is the intended production
tracker and can replace `IouTracker` without changing the worker — it produces
the same track-id-annotated Detections.
"""

from __future__ import annotations

from src.detection.types import Detection


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    """Intersection-over-union of two [x1, y1, x2, y2] boxes."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


class IouTracker:
    """Greedy IOU tracker keyed per class. Assigns stable track ids across
    frames while an object keeps overlapping; drops tracks after a miss budget."""

    def __init__(self, iou_threshold: float = 0.3, max_age: int = 5) -> None:
        self._iou_threshold = iou_threshold
        self._max_age = max_age
        self._next_id = 1
        # track_id -> (class_id, bbox, age)
        self._tracks: dict[int, tuple[int, tuple[float, float, float, float], int]] = {}

    def update(self, detections: list[Detection]) -> list[Detection]:
        """Assign track ids to detections (mutates their track_id)."""
        assigned: set[int] = set()

        for det in detections:
            best_id, best_iou = None, self._iou_threshold
            for tid, (cls, bbox, _age) in self._tracks.items():
                if tid in assigned or cls != det.class_id:
                    continue
                score = iou(det.bbox, bbox)
                if score >= best_iou:
                    best_id, best_iou = tid, score
            if best_id is None:
                best_id = self._next_id
                self._next_id += 1
            det.track_id = best_id
            assigned.add(best_id)
            self._tracks[best_id] = (det.class_id, det.bbox, 0)

        # Age out unmatched tracks.
        for tid in list(self._tracks):
            if tid not in assigned:
                cls, bbox, age = self._tracks[tid]
                if age + 1 > self._max_age:
                    del self._tracks[tid]
                else:
                    self._tracks[tid] = (cls, bbox, age + 1)

        return detections
