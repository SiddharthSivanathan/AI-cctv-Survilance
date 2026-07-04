"""Unit tests for the IOU tracker."""

from src.detection.tracker import IouTracker, iou
from src.detection.types import Detection


def _person(bbox) -> Detection:
    return Detection(0, "person", 0.9, bbox)


def test_iou_basic() -> None:
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0
    assert 0 < iou((0, 0, 10, 10), (5, 5, 15, 15)) < 1


def test_tracker_keeps_id_for_overlapping_object() -> None:
    tracker = IouTracker()
    d1 = tracker.update([_person((0, 0, 10, 10))])[0]
    d2 = tracker.update([_person((1, 1, 11, 11))])[0]  # moved slightly -> same track
    assert d1.track_id == d2.track_id


def test_tracker_new_id_for_new_object() -> None:
    tracker = IouTracker()
    tracker.update([_person((0, 0, 10, 10))])
    detections = tracker.update([_person((0, 0, 10, 10)), _person((100, 100, 110, 110))])
    ids = {d.track_id for d in detections}
    assert len(ids) == 2


def test_tracker_assigns_distinct_ids_same_frame() -> None:
    tracker = IouTracker()
    dets = tracker.update([_person((0, 0, 10, 10)), _person((50, 50, 60, 60))])
    assert dets[0].track_id != dets[1].track_id
