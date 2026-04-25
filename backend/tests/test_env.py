import numpy as np

from app.rl.env import ParkingEnv
from app.rl.presets import build_preset


def test_env_reset_observation_matches_space() -> None:
    env = ParkingEnv(build_preset("scene_easy"))

    observation, info = env.reset(seed=1)

    assert env.observation_space.contains(observation)
    assert info["step_count"] == 0


def test_env_step_returns_reward_and_info() -> None:
    env = ParkingEnv(build_preset("scene_easy"))
    env.reset(seed=1)

    observation, reward, terminated, truncated, info = env.step(
        np.array([0.1, 0.0], dtype=np.float32)
    )

    assert env.observation_space.contains(observation)
    assert isinstance(reward, float)
    assert not terminated
    assert not truncated
    assert "distance" in info

