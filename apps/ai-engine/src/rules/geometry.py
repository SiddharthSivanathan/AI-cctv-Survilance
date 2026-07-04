"""Geometry helpers for zone membership.

Zones are polygons drawn on the 640x640 sampled frame — the same coordinate
space as detection bounding boxes, so no rescaling is needed.
"""

from __future__ import annotations

Point = tuple[float, float]
Polygon = list[Point]


def foot_point(bbox: tuple[float, float, float, float]) -> Point:
    """Return the bottom-center of a bbox — the best proxy for where a person
    stands on the ground plane."""
    x1, _y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)


def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    """Ray-casting point-in-polygon test. Polygon is a list of (x, y) vertices."""
    if len(polygon) < 3:
        return False
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (
            (yj - yi) or 1e-12
        ) + xi
        if intersects:
            inside = not inside
        j = i
    return inside


def count_people_in_zone(
    person_boxes: list[tuple[float, float, float, float]], polygon: Polygon
) -> int:
    """Count person detections whose foot point lies inside the polygon."""
    return sum(1 for b in person_boxes if point_in_polygon(foot_point(b), polygon))
