from __future__ import annotations

from math import cos, sin, tan

from app.core.schemas import Action, CarSpec, CarState
from app.sim.geometry import normalize_angle


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def step_bicycle(state: CarState, action: Action, spec: CarSpec, dt: float) -> CarState:
    """Advance a center-referenced kinematic bicycle state by one fixed step."""
    v = state.v + action.acceleration * spec.max_accel * dt
    if action.acceleration == 0.0 and spec.drag > 0.0:
        v *= max(0.0, 1.0 - spec.drag * dt)
    v = _clip(v, spec.max_reverse_speed, spec.max_speed)

    delta = state.delta + action.steering_rate * spec.max_steer_rate * dt
    delta = _clip(delta, -spec.max_steer, spec.max_steer)

    theta_dot = v / spec.wheelbase * tan(delta)
    theta_next = normalize_angle(state.theta + theta_dot * dt)

    rear_x = state.x - spec.rear_axle_to_center * cos(state.theta)
    rear_y = state.y - spec.rear_axle_to_center * sin(state.theta)
    rear_x_next = rear_x + v * cos(state.theta) * dt
    rear_y_next = rear_y + v * sin(state.theta) * dt

    x_next = rear_x_next + spec.rear_axle_to_center * cos(theta_next)
    y_next = rear_y_next + spec.rear_axle_to_center * sin(theta_next)

    return CarState(x=x_next, y=y_next, theta=theta_next, v=v, delta=delta)

