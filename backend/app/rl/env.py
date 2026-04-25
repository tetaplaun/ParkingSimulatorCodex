from __future__ import annotations

from dataclasses import replace
from math import cos, sin
from typing import Any, cast

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from numpy.typing import NDArray

from app.core.schemas import Action, CarState, ParkingScene
from app.rl.reward import RewardConfig, compute_reward
from app.sim.bicycle import step_bicycle
from app.sim.geometry import normalize_angle
from app.sim.lidar import scan_lidar
from app.sim.scene import goal_metrics, has_collision, is_out_of_bounds, is_success

FloatArray = NDArray[np.float32]


class ParkingEnv(gym.Env[FloatArray, FloatArray]):
    metadata = {"render_modes": []}

    def __init__(
        self,
        scene: ParkingScene,
        *,
        reward_config: RewardConfig | None = None,
    ) -> None:
        super().__init__()
        self.scene = scene
        self.reward_config = reward_config or RewardConfig()
        self.state = scene.start
        self.step_count = 0
        self.previous_action = Action(acceleration=0.0, steering_rate=0.0)
        self._world_scale = max(
            scene.bounds.max_x - scene.bounds.min_x,
            scene.bounds.max_y - scene.bounds.min_y,
        )

        observation_size = scene.lidar.rays + 10
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(observation_size,),
            dtype=np.float32,
        )
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[FloatArray, dict[str, Any]]:
        super().reset(seed=seed)
        self.state = self.scene.start
        self.step_count = 0
        self.previous_action = Action(acceleration=0.0, steering_rate=0.0)
        return self._observation(), self._info()

    def step(
        self,
        action_array: FloatArray,
    ) -> tuple[FloatArray, float, bool, bool, dict[str, Any]]:
        acceleration, steering_rate = np.clip(action_array, -1.0, 1.0).astype(float)
        action = Action(acceleration=acceleration, steering_rate=steering_rate)
        previous_state = self.state

        self.state = step_bicycle(previous_state, action, self.scene.car_spec, self.scene.dt)
        self.step_count += 1

        collision = has_collision(self.scene, self.state)
        out_of_bounds = is_out_of_bounds(self.scene, self.state)
        success = is_success(self.scene, self.state)
        terminated = success or collision or out_of_bounds
        truncated = self.step_count >= self.scene.max_steps
        reward = compute_reward(
            self.scene,
            previous_state,
            self.state,
            action,
            collision=collision,
            out_of_bounds=out_of_bounds,
            success=success,
            config=self.reward_config,
        )
        if truncated and not terminated:
            metrics = goal_metrics(self.scene, self.state)
            timeout_penalty = min(
                120.0,
                self.reward_config.timeout_base_penalty
                + self.reward_config.timeout_distance_weight * metrics.distance,
            )
            reward = replace(reward, total=reward.total - timeout_penalty)
        self.previous_action = action

        info = self._info()
        info.update(
            {
                "reward_breakdown": reward,
                "collision": collision,
                "out_of_bounds": out_of_bounds,
                "success": success,
            }
        )
        return self._observation(), float(reward.total), terminated, truncated, info

    def _observation(self) -> FloatArray:
        state = self.state
        goal = self.scene.goal
        dx = goal.x - state.x
        dy = goal.y - state.y
        ego_x = dx * cos(state.theta) + dy * sin(state.theta)
        ego_y = -dx * sin(state.theta) + dy * cos(state.theta)
        heading_error = normalize_angle(goal.theta - state.theta)

        rear_x = state.x - self.scene.car_spec.rear_axle_to_center * cos(state.theta)
        rear_y = state.y - self.scene.car_spec.rear_axle_to_center * sin(state.theta)
        rear_dx = goal.x - rear_x
        rear_dy = goal.y - rear_y
        rear_ego_x = rear_dx * cos(state.theta) + rear_dy * sin(state.theta)
        rear_ego_y = -rear_dx * sin(state.theta) + rear_dy * cos(state.theta)

        lidar = np.array(scan_lidar(self.scene, state), dtype=np.float32)
        lidar = np.clip(lidar / self.scene.lidar.max_distance, 0.0, 1.0)
        extra = np.array(
            [
                ego_x / self._world_scale,
                ego_y / self._world_scale,
                sin(heading_error),
                cos(heading_error),
                state.v / self.scene.car_spec.max_speed,
                state.delta / self.scene.car_spec.max_steer,
                self.previous_action.acceleration,
                self.previous_action.steering_rate,
                rear_ego_x / self._world_scale,
                rear_ego_y / self._world_scale,
            ],
            dtype=np.float32,
        )
        observation = np.clip(np.concatenate([lidar, extra]), -1.0, 1.0).astype(np.float32)
        return cast(FloatArray, observation)

    def _info(self) -> dict[str, Any]:
        metrics = goal_metrics(self.scene, self.state)
        return {
            "step_count": self.step_count,
            "state": self.state,
            "distance": metrics.distance,
            "heading_error": metrics.heading_error,
            "speed": metrics.speed,
            "steering": metrics.steering,
        }


def state_to_action_array(action: Action) -> FloatArray:
    return np.array([action.acceleration, action.steering_rate], dtype=np.float32)


def state_from_array(values: FloatArray) -> CarState:
    return CarState(
        x=float(values[0]),
        y=float(values[1]),
        theta=float(values[2]),
        v=float(values[3]),
        delta=float(values[4]),
    )
