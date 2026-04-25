from __future__ import annotations

from dataclasses import dataclass

from app.core.schemas import Action, CarState, ParkingScene
from app.sim.scene import goal_metrics


@dataclass(frozen=True)
class RewardConfig:
    gamma: float = 1.0
    distance_weight: float = 4.0
    heading_weight: float = 0.8
    speed_weight: float = 0.2
    time_cost: float = 0.03
    effort_cost: float = 0.015
    success_reward: float = 120.0
    collision_penalty: float = -120.0
    out_of_bounds_penalty: float = -120.0
    timeout_base_penalty: float = 20.0
    timeout_distance_weight: float = 20.0


@dataclass(frozen=True)
class RewardBreakdown:
    total: float
    shaping: float
    terminal: float
    time: float
    effort: float


def potential(scene: ParkingScene, state: CarState, config: RewardConfig) -> float:
    metrics = goal_metrics(scene, state)
    return -(
        config.distance_weight * metrics.distance
        + config.heading_weight * metrics.heading_error
        + config.speed_weight * metrics.speed
    )


def compute_reward(
    scene: ParkingScene,
    previous_state: CarState,
    next_state: CarState,
    action: Action,
    *,
    collision: bool,
    out_of_bounds: bool,
    success: bool,
    config: RewardConfig | None = None,
) -> RewardBreakdown:
    reward_config = config or RewardConfig()
    shaping = reward_config.gamma * potential(scene, next_state, reward_config) - potential(
        scene,
        previous_state,
        reward_config,
    )
    terminal = 0.0
    if success:
        terminal += reward_config.success_reward
    if collision:
        terminal += reward_config.collision_penalty
    if out_of_bounds:
        terminal += reward_config.out_of_bounds_penalty

    time = -reward_config.time_cost
    effort = -reward_config.effort_cost * (
        abs(action.acceleration) + abs(action.steering_rate)
    )
    total = shaping + terminal + time + effort
    return RewardBreakdown(
        total=total,
        shaping=shaping,
        terminal=terminal,
        time=time,
        effort=effort,
    )
