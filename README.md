# ParkingSimulator Codex

Clean-start implementation of the ParkingSimulator plan in `PLAN_CODEX_VERSION.md`.

## Layout

```text
backend/   Python API, schemas, simulator, RL/lab code
frontend/  Vite React browser app
```

## Backend

```bash
cd backend
uv sync
uv run pytest
uv run ruff check .
uv run mypy app
uv run uvicorn app.api.main:app --reload
```

## Training Lab

```bash
cd backend
uv run python -m app.lab.train --preset scene_easy --algo ppo --seed 42 --total-timesteps 100000 --promote
uv run python -m app.lab.evaluate --preset scene_easy --policy policies/scene_easy.zip --algo ppo --episodes 50
uv run python -m app.lab.diagnose --preset scene_easy --policy policies/scene_easy.zip --algo ppo --episodes 3
```

Training writes immutable run policies to `backend/policies/` and manifests to
`backend/runs/<run_id>/manifest.json`. A policy is copied to
`backend/policies/<preset>.zip` only when `--promote` is used and deterministic
evaluation reaches at least 90% success for that run.

## Frontend

```bash
cd frontend
npm install
npm run typecheck
npm run build
npm run dev
```
