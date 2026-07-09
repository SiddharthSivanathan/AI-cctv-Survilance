"""Multi-object tracking.

Production tracking uses ByteTrack (via `supervision`) — `ByteTrackTracker`.
A deterministic, dependency-free IOU tracker (`IouTracker`) remains as a
unit-testable fallback used when supervision/numpy are unavailable. Both share
the same interface: ``update(detections) -> detections`` (track ids assigned in
place), so the worker is agnostic to which one it holds.
"""

from __future__ import annotations

import structlog

from src.detection.types import Detection

logger = structlog.get_logger("tracker")

# Common protocol: any tracker exposes ``update(list[Detection]) -> list[Detection]``.


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


class ByteTrackTracker:
    """ByteTrack multi-object tracker (via the ``supervision`` library).

    Stateful per camera: keep one instance per camera stream. Assigns stable
    track ids across frames, handling occlusions/misses far better than the
    greedy IOU tracker. Same interface as ``IouTracker``.
    """

    def __init__(self) -> None:
        import warnings

        import supervision as sv  # lazy: pulls numpy

        # sv.ByteTrack is deprecated in supervision 0.29 (removed in 0.30) but is
        # the ByteTrack implementation shipped today; pyproject pins <0.30.
        # minimum_consecutive_frames=1 assigns a track id on first sighting —
        # the default withholds ids for several frames, which at low sample FPS
        # leaves most detections id-less. lost_track_buffer keeps ids stable
        # across brief occlusions/misses.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self._tracker = sv.ByteTrack(
                minimum_consecutive_frames=1,
                lost_track_buffer=60,
            )
        self._sv = sv

    def update(self, detections: list[Detection]) -> list[Detection]:
        import numpy as np

        if not detections:
            # Still advance the tracker so lost tracks age out correctly.
            self._tracker.update_with_detections(self._sv.Detections.empty())
            return detections

        sv_det = self._sv.Detections(
            xyxy=np.array([d.bbox for d in detections], dtype=float),
            confidence=np.array([d.confidence for d in detections], dtype=float),
            class_id=np.array([d.class_id for d in detections], dtype=int),
        )
        tracked = self._tracker.update_with_detections(sv_det)

        # Map assigned track ids back onto our Detection objects by bbox. ByteTrack
        # may not confirm every detection on its first frame; those stay id-less.
        by_box: dict[tuple, int] = {}
        if tracked.tracker_id is not None:
            for box, tid in zip(tracked.xyxy, tracked.tracker_id, strict=False):
                by_box[tuple(round(float(v), 2) for v in box)] = int(tid)
        for det in detections:
            det.track_id = by_box.get(tuple(round(float(v), 2) for v in det.bbox))
        return detections


def make_tracker():
    """Return the best available tracker: ByteTrack if supervision imports,
    else the pure-Python IOU tracker (keeps the engine working headless/in tests)."""
    try:
        return ByteTrackTracker()
    except Exception as exc:  # noqa: BLE001 - fall back rather than crash the worker
        logger.warning("bytetrack_unavailable_falling_back_to_iou", error=str(exc))
        return IouTracker()
