"""Unit tests for detection parsing + payload building (no ML deps)."""

from src.config import DEFAULT_CLASSES
from src.detection.detector import parse_results
from src.detection.types import Detection
from src.pipeline.worker import build_payload

ALLOWED = set(DEFAULT_CLASSES)


def test_parse_results_filters_by_class_and_confidence() -> None:
    rows = [
        [0, 0, 10, 20, 0.9, 0],  # person, high conf -> kept
        [0, 0, 5, 5, 0.2, 0],  # person, low conf -> dropped
        [0, 0, 5, 5, 0.9, 15],  # class 15 (cat) not allowed -> dropped
        [1, 1, 9, 9, 0.8, 2],  # car -> kept
    ]
    dets = parse_results(rows, class_map=DEFAULT_CLASSES, allowed_ids=ALLOWED, min_confidence=0.35)
    assert len(dets) == 2
    assert {d.class_name for d in dets} == {"person", "car"}


def test_build_payload_counts_people() -> None:
    dets = [
        Detection(0, "person", 0.9, (0, 0, 1, 1), track_id=1),
        Detection(0, "person", 0.8, (2, 2, 3, 3), track_id=2),
        Detection(2, "car", 0.7, (4, 4, 5, 5), track_id=3),
    ]
    payload = build_payload("cam-1", dets, ts=123.0)
    assert payload["camera_id"] == "cam-1"
    assert payload["person_count"] == 2
    assert len(payload["detections"]) == 3
    assert payload["detections"][0]["track_id"] == 1
