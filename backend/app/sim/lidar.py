from __future__ import annotations

from math import cos, sin

from app.core.schemas import CarState, ParkingScene
from app.sim.geometry import OrientedBox, box_corners, ray_polygon_distance
from app.sim.scene import obstacle_box


def _bounds_points(scene: ParkingScene) -> list[tuple[float, float]]:
    bounds = scene.bounds
    return [
        (bounds.max_x, bounds.max_y),
        (bounds.max_x, bounds.min_y),
        (bounds.min_x, bounds.min_y),
        (bounds.min_x, bounds.max_y),
    ]


def scan_lidar(scene: ParkingScene, state: CarState) -> list[float]:
    config = scene.lidar
    if config.rays == 1:
        offsets = [0.0]
    else:
        start = -config.fov / 2.0
        step = config.fov / (config.rays - 1)
        offsets = [start + index * step for index in range(config.rays)]

    polygons = [_bounds_points(scene)]
    polygons.extend(box_corners(obstacle_box(obstacle)) for obstacle in scene.obstacles)

    distances: list[float] = []
    origin = (state.x, state.y)
    for offset in offsets:
        angle = state.theta + offset
        direction = (cos(angle), sin(angle))
        ray_distance = config.max_distance
        for polygon in polygons:
            hit = ray_polygon_distance(origin, direction, polygon)
            if hit is not None:
                ray_distance = min(ray_distance, hit)
        distances.append(ray_distance)
    return distances


def lidar_box_from_state(scene: ParkingScene, state: CarState) -> OrientedBox:
    return OrientedBox(
        x=state.x,
        y=state.y,
        length=scene.car_spec.length,
        width=scene.car_spec.width,
        theta=state.theta,
    )

