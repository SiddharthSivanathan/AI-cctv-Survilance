"""Unit tests for zone geometry."""

from src.rules.geometry import count_people_in_zone, foot_point, point_in_polygon

SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]


def test_point_in_polygon() -> None:
    assert point_in_polygon((5, 5), SQUARE)
    assert not point_in_polygon((15, 5), SQUARE)
    assert not point_in_polygon((5, 5), [(0, 0), (1, 1)])  # degenerate


def test_foot_point_is_bottom_center() -> None:
    assert foot_point((0, 0, 10, 20)) == (5.0, 20.0)


def test_count_people_in_zone_uses_foot_point() -> None:
    # foot point (5, 10) sits on the bottom edge -> inside; (5, 30) is below.
    boxes = [(0, 0, 10, 9), (0, 20, 10, 30)]
    assert count_people_in_zone(boxes, SQUARE) == 1
