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


def side_of_line(point: Point, a: Point, b: Point) -> int:
    """Which side of the directed line A->B the point is on.

    Returns +1 (left of A->B), -1 (right), or 0 (on the line), via the sign of
    the 2D cross product. Used to detect line crossings by watching a tracked
    object's side flip between frames.
    """
    cross = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
    if cross > 0:
        return 1
    if cross < 0:
        return -1
    return 0
