from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EvalSummary(BaseModel):
    episodes: int
    success_rate: float
    collision_rate: float
    out_of_bounds_rate: float
    timeout_rate: float
    mean_return: float
    mean_length: float
    mean_final_distance: float
    mean_final_heading_error: float
    mean_final_speed: float


class RunManifest(BaseModel):
    run_id: str
    preset: str
    algorithm: str
    seed: int
    total_timesteps: int
    started_at: str
    completed_at: str
    policy_path: str
    reward_version: str = "potential_v1"
    curriculum_stage: str = "fixed_scene"
    warm_start: str | None = None
    eval: EvalSummary | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def make_run_id(preset: str, algorithm: str, seed: int) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{preset}_{algorithm}_seed{seed}_{timestamp}".replace("-", "_")


def write_manifest(path: Path, manifest: RunManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

