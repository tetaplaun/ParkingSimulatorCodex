from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from app.lab.evaluate import load_model
from app.rl.env import ParkingEnv
from app.rl.presets import build_preset


def main() -> None:
    parser = argparse.ArgumentParser(description="Print short rollout diagnostics for a policy.")
    parser.add_argument("--preset", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--algo", choices=("ppo", "sac"), default=None)
    parser.add_argument("--episodes", type=int, default=3)
    args = parser.parse_args()

    scene = build_preset(args.preset)
    env = ParkingEnv(scene)
    model = load_model(args.policy, args.algo)

    for episode in range(args.episodes):
        obs, _ = env.reset(seed=episode)
        done = False
        last_info: dict[str, Any] = {}
        total_reward = 0.0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, last_info = env.step(
                np.asarray(action, dtype=np.float32)
            )
            total_reward += reward
            done = terminated or truncated

        print(
            "episode={episode} success={success} collision={collision} "
            "out_of_bounds={out_of_bounds} steps={steps} return={return_:.2f} "
            "distance={distance:.3f} heading={heading:.3f} speed={speed:.3f}".format(
                episode=episode,
                success=last_info.get("success", False),
                collision=last_info.get("collision", False),
                out_of_bounds=last_info.get("out_of_bounds", False),
                steps=int(last_info.get("step_count", 0)),
                return_=total_reward,
                distance=float(last_info.get("distance", 0.0)),
                heading=float(last_info.get("heading_error", 0.0)),
                speed=float(last_info.get("speed", 0.0)),
            )
        )


if __name__ == "__main__":
    main()
