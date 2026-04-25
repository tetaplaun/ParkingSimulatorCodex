from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from stable_baselines3.common.base_class import BaseAlgorithm

from app.core.schemas import Action, ReplayRequest, ReplayResult, SimStep
from app.lab.evaluate import load_model
from app.rl.presets import PRESET_KEYS, build_preset
from app.sim.replay import replay
from app.sim.scene import goal_metrics
from app.sim.scripted import has_scripted_replay, scripted_replay

app = FastAPI(title="ParkingSimulator Codex API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
POLICY_DIR = Path("policies")


class ReplayWithSource(BaseModel):
    source: Literal["trained_policy", "scripted_teacher"]
    replay: ReplayResult


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/presets")
def list_presets() -> dict[str, tuple[str, ...]]:
    return {"presets": PRESET_KEYS}


@app.get("/policies")
def list_policies() -> dict[str, list[str]]:
    if not POLICY_DIR.exists():
        return {"policies": []}
    policies = sorted(path.stem for path in POLICY_DIR.glob("*.zip"))
    return {"policies": policies}


@app.get("/presets/{preset_key}")
def get_preset(preset_key: str) -> dict[str, object]:
    if preset_key not in PRESET_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset_key}")
    return build_preset(preset_key).model_dump()


@app.post("/replay")
def replay_scene(request: ReplayRequest) -> ReplayResult:
    return replay(request.scene, request.actions, include_lidar=request.include_lidar)


@lru_cache(maxsize=16)
def _load_policy(policy_path: str) -> BaseAlgorithm:
    return load_model(Path(policy_path), algo="ppo")


def _rollout_policy(preset_key: str, include_lidar: bool = False) -> ReplayResult:
    scene = build_preset(preset_key)
    policy_path = POLICY_DIR / f"{preset_key}.zip"
    model = _load_policy(str(policy_path))
    state = scene.start
    steps: list[SimStep] = []
    reason = "timeout"
    success = False
    terminated = False

    from app.rl.env import ParkingEnv

    env = ParkingEnv(scene)
    obs, _ = env.reset(seed=0)
    for index in range(1, scene.max_steps + 1):
        action_array, _ = model.predict(obs, deterministic=True)
        action_values = np.clip(np.asarray(action_array, dtype=np.float32), -1.0, 1.0)
        action = Action(
            acceleration=float(action_values[0]),
            steering_rate=float(action_values[1]),
        )
        obs, _reward, env_terminated, env_truncated, info = env.step(action_values)
        state = env.state
        success = bool(info.get("success", False))
        collision = bool(info.get("collision", False))
        out_of_bounds = bool(info.get("out_of_bounds", False))

        steps.append(
            SimStep(
                index=index,
                state=state,
                action=action,
                metrics=goal_metrics(scene, state),
                collision=collision,
                out_of_bounds=out_of_bounds,
                success=success,
                lidar_distances=None if not include_lidar else [],
            )
        )

        if success:
            reason = "success"
            terminated = True
            break
        if collision:
            reason = "collision"
            terminated = True
            break
        if out_of_bounds:
            reason = "out_of_bounds"
            terminated = True
            break
        if env_terminated or env_truncated:
            terminated = env_terminated
            break

    return ReplayResult(
        scene_id=scene.id,
        steps=steps,
        final_state=state,
        reason=reason,
        success=success,
        terminated=terminated,
    )


@app.get("/policies/{preset_key}/replay")
def replay_policy(preset_key: str, include_lidar: bool = False) -> ReplayResult:
    if preset_key not in PRESET_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset_key}")

    policy_path = POLICY_DIR / f"{preset_key}.zip"
    if not policy_path.exists():
        raise HTTPException(status_code=404, detail=f"No promoted policy for preset: {preset_key}")

    return _rollout_policy(preset_key, include_lidar=include_lidar)


@app.get("/replays/{preset_key}/best")
def replay_best(preset_key: str, include_lidar: bool = False) -> ReplayWithSource:
    if preset_key not in PRESET_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset_key}")

    policy_path = POLICY_DIR / f"{preset_key}.zip"
    if policy_path.exists():
        return ReplayWithSource(
            source="trained_policy",
            replay=_rollout_policy(preset_key, include_lidar=include_lidar),
        )

    if has_scripted_replay(preset_key):
        return ReplayWithSource(
            source="scripted_teacher",
            replay=scripted_replay(
                preset_key,
                build_preset(preset_key),
                include_lidar=include_lidar,
            ),
        )

    raise HTTPException(status_code=404, detail=f"No replay source for preset: {preset_key}")
