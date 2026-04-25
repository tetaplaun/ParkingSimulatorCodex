from __future__ import annotations

import argparse
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stable_baselines3 import PPO, SAC
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.monitor import Monitor

from app.lab.evaluate import evaluate_policy, load_model
from app.lab.manifests import RunManifest, make_run_id, write_manifest
from app.rl.env import ParkingEnv
from app.rl.presets import build_preset


def build_model(algo: str, env: Any, seed: int) -> BaseAlgorithm:
    if algo == "ppo":
        return PPO(
            "MlpPolicy",
            env,
            seed=seed,
            gamma=0.99,
            learning_rate=3e-4,
            n_steps=1024,
            batch_size=64,
            n_epochs=8,
            verbose=1,
        )
    if algo == "sac":
        return SAC(
            "MlpPolicy",
            env,
            seed=seed,
            gamma=0.99,
            learning_rate=3e-4,
            buffer_size=100_000,
            learning_starts=1_000,
            batch_size=128,
            train_freq=1,
            gradient_steps=1,
            verbose=1,
        )
    raise ValueError(f"Unsupported algorithm: {algo}")


def train_policy(
    *,
    preset: str,
    algo: str,
    seed: int,
    total_timesteps: int,
    output_dir: Path,
    runs_dir: Path,
    eval_episodes: int,
    promote: bool,
    warm_start: Path | None,
) -> RunManifest:
    started_at = datetime.now(UTC).isoformat()
    scene = build_preset(preset)
    run_id = make_run_id(preset, algo, seed)
    run_dir = runs_dir / run_id
    policy_path = output_dir / f"{run_id}.zip"

    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    env: Any = Monitor(ParkingEnv(scene), filename=str(run_dir / "monitor.csv"))
    if warm_start is None:
        model = build_model(algo, env, seed)
    else:
        model = load_model(warm_start, algo=algo)
        model.set_env(env)
    model.learn(total_timesteps=total_timesteps, progress_bar=False)
    model.save(policy_path)

    eval_summary = evaluate_policy(
        policy_path,
        preset,
        episodes=eval_episodes,
        deterministic=True,
        seed=seed + 10_000,
        algo=algo,
    )
    completed_at = datetime.now(UTC).isoformat()
    manifest = RunManifest(
        run_id=run_id,
        preset=preset,
        algorithm=algo,
        seed=seed,
        total_timesteps=total_timesteps,
        started_at=started_at,
        completed_at=completed_at,
        policy_path=str(policy_path),
        warm_start=str(warm_start) if warm_start is not None else None,
        eval=eval_summary,
    )
    write_manifest(run_dir / "manifest.json", manifest)

    if promote and eval_summary.success_rate >= 0.9:
        champion_path = output_dir / f"{preset}.zip"
        if champion_path.exists():
            archive_dir = output_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived = archive_dir / f"{champion_path.stem}_{run_id}.zip"
            shutil.copy2(champion_path, archived)
        shutil.copy2(policy_path, champion_path)

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a parking policy.")
    parser.add_argument("--preset", required=True)
    parser.add_argument("--algo", choices=("ppo", "sac"), default="ppo")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-timesteps", type=int, default=20_000)
    parser.add_argument("--output-dir", type=Path, default=Path("policies"))
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--eval-episodes", type=int, default=10)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--warm-start", type=Path, default=None)
    args = parser.parse_args()

    manifest = train_policy(
        preset=args.preset,
        algo=args.algo,
        seed=args.seed,
        total_timesteps=args.total_timesteps,
        output_dir=args.output_dir,
        runs_dir=args.runs_dir,
        eval_episodes=args.eval_episodes,
        promote=args.promote,
        warm_start=args.warm_start,
    )
    print(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
