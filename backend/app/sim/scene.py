from __future__ import annotations

from math import hypot

from app.core.schemas import CarState, GoalMetrics, ParkingScene, RectObstacle
from app.sim.geometry import OrientedBox, box_corners, normalize_angle, obb_intersects


def car_box(scene: ParkingScene, state: CarState) -> OrientedBox:
    spec = scene.car_spec
    return OrientedBox(
        x=state.x,
        y=state.y,
        length=spec.length,
        width=spec.width,
        theta=state.theta,
    )


def obstacle_box(obstacle: RectObstacle) -> OrientedBox:
    return OrientedBox(
        x=obstacle.x,
        y=obstacle.y,
        length=obstacle.width,
        width=obstacle.height,
        theta=obstacle.theta,
    )


def is_out_of_bounds(scene: ParkingScene, state: CarState) -> bool:
    bounds = scene.bounds
    return any(
        x < bounds.min_x or x > bounds.max_x or y < bounds.min_y or y > bounds.max_y
        for x, y in box_corners(car_box(scene, state))
    )


def has_collision(scene: ParkingScene, state: CarState) -> bool:
    vehicle = car_box(scene, state)
    return any(obb_intersects(vehicle, obstacle_box(obstacle)) for obstacle in scene.obstacles)


def goal_metrics(scene: ParkingScene, state: CarState) -> GoalMetrics:
    return GoalMetrics(
        distance=hypot(state.x - scene.goal.x, state.y - scene.goal.y),
        heading_error=abs(normalize_angle(state.theta - scene.goal.theta)),
        speed=abs(state.v),
        steering=abs(state.delta),
    )


def is_success(scene: ParkingScene, state: CarState) -> bool:
    metrics = goal_metrics(scene, state)
    criteria = scene.success
    steering_ok = (
        True
        if criteria.steering_tolerance is None
        else metrics.steering <= criteria.steering_tolerance
    )
    return (
        metrics.distance <= criteria.distance_tolerance
        and metrics.heading_error <= criteria.heading_tolerance
        and metrics.speed <= criteria.speed_tolerance
        and steering_ok
        and not has_collision(scene, state)
        and not is_out_of_bounds(scene, state)
    )

