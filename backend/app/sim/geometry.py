from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

Point = tuple[float, float]
Vector = tuple[float, float]


@dataclass(frozen=True)
class OrientedBox:
    x: float
    y: float
    length: float
    width: float
    theta: float


def normalize_angle(angle: float) -> float:
    while angle <= -pi:
        angle += 2 * pi
    while angle > pi:
        angle -= 2 * pi
    return angle


def rotate(point: Point, theta: float) -> Point:
    x, y = point
    return (x * cos(theta) - y * sin(theta), x * sin(theta) + y * cos(theta))


def box_corners(box: OrientedBox) -> list[Point]:
    half_l = box.length / 2.0
    half_w = box.width / 2.0
    local = [
        (half_l, half_w),
        (half_l, -half_w),
        (-half_l, -half_w),
        (-half_l, half_w),
    ]
    return [(box.x + dx, box.y + dy) for dx, dy in (rotate(point, box.theta) for point in local)]


def box_axes(box: OrientedBox) -> list[Vector]:
    return [(cos(box.theta), sin(box.theta)), (-sin(box.theta), cos(box.theta))]


def _project(points: list[Point], axis: Vector) -> tuple[float, float]:
    dots = [point[0] * axis[0] + point[1] * axis[1] for point in points]
    return min(dots), max(dots)


def _overlaps(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def obb_intersects(left: OrientedBox, right: OrientedBox) -> bool:
    left_points = box_corners(left)
    right_points = box_corners(right)
    for axis in [*box_axes(left), *box_axes(right)]:
        if not _overlaps(_project(left_points, axis), _project(right_points, axis)):
            return False
    return True


def polygon_edges(points: list[Point]) -> list[tuple[Point, Point]]:
    return list(zip(points, [*points[1:], points[0]], strict=True))


def ray_segment_distance(
    origin: Point,
    direction: Vector,
    start: Point,
    end: Point,
) -> float | None:
    ox, oy = origin
    dx, dy = direction
    sx, sy = start
    ex, ey = end
    vx = ex - sx
    vy = ey - sy
    cross = dx * vy - dy * vx
    if abs(cross) < 1e-12:
        return None

    qx = sx - ox
    qy = sy - oy
    ray_t = (qx * vy - qy * vx) / cross
    segment_t = (qx * dy - qy * dx) / cross
    if ray_t >= 0.0 and 0.0 <= segment_t <= 1.0:
        return ray_t
    return None


def ray_polygon_distance(origin: Point, direction: Vector, points: list[Point]) -> float | None:
    distances = [
        distance
        for start, end in polygon_edges(points)
        if (distance := ray_segment_distance(origin, direction, start, end)) is not None
    ]
    return min(distances) if distances else None
