from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.base_class import BaseAlgorithm

from app.lab.manifests import EvalSummary
from app.rl.env import ParkingEnv
from app.rl.presets import build_preset


def load_model(policy_path: Path, algo: str | None = None) -> BaseAlgorithm:
    algorithm = (algo or _infer_algorithm(policy_path)).lower()
    if algorithm == "sac":
        return SAC.load(policy_path)
    if algorithm == "ppo":
        return PPO.load(policy_path)
    raise ValueError(f"Unsupported algorithm: {algorithm}")


def _infer_algorithm(policy_path: Path) -> str:
    stem = policy_path.stem.lower()
    if "_sac_" in stem or stem.endswith("_sac"):
        return "sac"
    return "ppo"


def evaluate_policy(
    policy_path: Path,
    preset: str,
    *,
    episodes: int = 50,
    deterministic: bool = True,
    seed: int = 0,
    algo: str | None = None,
) -> EvalSummary:
    scene = build_preset(preset)
    env = ParkingEnv(scene)
    model = load_model(policy_path, algo=algo)

    returns: list[float] = []
    lengths: list[int] = []
    final_distances: list[float] = []
    final_headings: list[float] = []
    final_speeds: list[float] = []
    successes = 0
    collisions = 0
    out_of_bounds = 0
    timeouts = 0

    for episode in range(episodes):
        obs, info = env.reset(seed=seed + episode)
        done = False
        episode_return = 0.0
        length = 0
        last_info: dict[str, Any] = info
        while not done:
            action, _ = model.predict(obs, deterministic=deterministic)
            obs, reward, terminated, truncated, last_info = env.step(
                np.asarray(action, dtype=np.float32)
            )
            episode_return += reward
            length += 1
            done = terminated or truncated

        returns.append(episode_return)
        lengths.append(length)
        final_distances.append(float(last_info["distance"]))
        final_headings.append(float(last_info["heading_error"]))
        final_speeds.append(float(last_info["speed"]))
        successes += int(bool(last_info.get("success", False)))
        collisions += int(bool(last_info.get("collision", False)))
        out_of_bounds += int(bool(last_info.get("out_of_bounds", False)))
        failed_terminal = (
            not last_info.get("success", False)
            and not last_info.get("collision", False)
            and not last_info.get("out_of_bounds", False)
        )
        timeouts += int(failed_terminal)

    return EvalSummary(
        episodes=episodes,
        success_rate=successes / episodes,
        collision_rate=collisions / episodes,
        out_of_bounds_rate=out_of_bounds / episodes,
        timeout_rate=timeouts / episodes,
        mean_return=float(np.mean(returns)),
        mean_length=float(np.mean(lengths)),
        mean_final_distance=float(np.mean(final_distances)),
        mean_final_heading_error=float(np.mean(final_headings)),
        mean_final_speed=float(np.mean(final_speeds)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained parking policy.")
    parser.add_argument("--preset", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--algo", choices=("ppo", "sac"), default=None)
    parser.add_argument("--stochastic", action="store_true")
    args = parser.parse_args()

    summary = evaluate_policy(
        args.policy,
        args.preset,
        episodes=args.episodes,
        deterministic=not args.stochastic,
        seed=args.seed,
        algo=args.algo,
    )
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
