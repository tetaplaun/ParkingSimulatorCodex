# ParkingSimulator Codex Version Plan

This is a clean-start plan for a Codex-built version of ParkingSimulator. It uses
the current project as a case study, but it is not a copy plan. The goal is to
build the same product idea with a better training architecture from day one.

## 1. Product Goal

Build a 2D browser app where a user can create or select a parking scene, run or
replay an autonomous parking policy, and inspect why the policy succeeded or
failed.

The core experience should be:

1. Edit a parking scene visually.
2. Pick a maneuver family or preset.
3. Replay a trained policy immediately.
4. Optionally launch training or fine-tuning and watch progress.
5. Export scenes, trajectories, policies, and diagnostics.

The important product shift from the current implementation: do not depend on
"train from scratch on this one arbitrary scene" as the primary happy path.
Training from scratch is a research/lab feature. The product should use robust
generalist or warm-started policies for interactive demos.

## 2. What I Would Do Differently

### 2.1 Build the Training Lab Before the Live Demo

The current project reached useful conclusions only after many ad-hoc runs were
documented in `PLAN.md`. In a restart, create the experiment harness first:

- fixed benchmark scenes;
- deterministic evaluation;
- per-criterion failure counts;
- trajectory export;
- run manifests;
- seed sweeps;
- automatic champion selection;
- artifact naming that records recipe, seed, and eval score.

The browser should consume policy artifacts produced by this lab. Live training
can come later.

### 2.2 Treat Parking as a Family of Tasks, Not One Scene at a Time

The hard presets failed when PPO had to discover a precise maneuver from a
single geometry. Train over distributions:

- parallel slots with varying width, curb distance, approach offset, start pose;
- perpendicular slots with varying width and aisle depth;
- reverse-garage slots with gradually increasing turn complexity;
- distractor obstacle layouts.

Then fine-tune a policy onto a specific scene only when needed.

### 2.3 Use Geometry Curriculum, Not Random Disk Curriculum

The current disk-radius curriculum spread episodes too thinly and sometimes
sampled invalid poses. Prefer curriculum by scene morphology:

- wide slot -> medium slot -> target slot;
- short approach -> full approach;
- low heading error -> full heading error;
- no obstacles -> flanking obstacles -> curb/wall;
- already-aligned reverse start -> full three-point-turn start.

This keeps the task identity stable while gradually tightening the skill.

### 2.4 Use Real Policy Warm-Starts as a First-Class Strategy

The biggest empirical win in the current project was:

```text
easy sibling policy -> hard target fine-tune
```

For the Codex version, make this the default training strategy:

- train `easy-parallel`;
- fine-tune `parallel`;
- train `easy-perpendicular`;
- fine-tune `perpendicular`;
- train `easy-reverse-garage`;
- fine-tune `reverse-garage`;
- train intermediate slot widths for `tight-squeeze`.

Do not wait until late-stage debugging to introduce these siblings.

### 2.5 Do Not Trust BC Unless It Can Drive Standalone

The current BC checkpoints fit demo actions but crashed during rollout. In the
new version, a BC policy is not allowed to be used as a warm-start unless it
passes rollout evaluation on its own scene.

Minimum BC gate:

- deterministic success rate >= 50% on the demo scene, or
- stochastic success rate >= 50% over 50 episodes, or
- demonstrably reaches the goal region without collision in diagnostics.

If it fails, do not fine-tune from it.

### 2.6 Avoid Positive Per-Step Rewards That Make Camping Profitable

The existing proximity bonus made "sit near the goal but not succeed" too
attractive in some geometries. Use potential-based shaping instead:

```text
r = terminal_success
  + terminal_collision
  + gamma * Phi(s_next) - Phi(s)
  - time_cost
  - effort_cost
  - no_progress_penalty
```

Potential terms can include distance, heading error, speed near goal, and rear
axle alignment. The key property is that parking successfully must dominate
stalling near the goal.

### 2.7 Consider Off-Policy RL for the Main Lab

PPO is easy to stream and stable enough, but it is sample-inefficient for this
continuous-control problem. The Codex version should support:

- SAC as the default lab algorithm for continuous actions;
- PPO as an optional live-demo baseline;
- behavior cloning pretraining when a teacher dataset is available;
- fine-tuning from existing policy checkpoints.

Start with Stable-Baselines3 SAC/PPO before adding new RL frameworks.

### 2.8 Add a Teacher Before Asking RL to Discover Everything

For hard maneuvers, add a geometric teacher:

- Hybrid A* or lattice planner for car-like paths;
- simple pure-pursuit or Stanley controller to follow planned paths;
- scripted waypoint controllers for easy sibling scenes;
- generated demonstrations for BC and DAgger-style correction.

The teacher does not need to be perfect. It needs to produce enough successful
or near-successful trajectories that RL starts inside the right behavior basin.

## 3. Recommended Stack

### Backend

- Python 3.11 or 3.12.
- `uv` for dependency management.
- FastAPI for API and WebSocket streaming.
- Pydantic v2 schemas.
- NumPy for deterministic simulation.
- Gymnasium environment.
- Stable-Baselines3 for PPO and SAC.
- PyTorch.
- pytest, ruff, mypy.

### Frontend

- Next.js or Vite React.
- TypeScript.
- Zustand for editor state.
- TanStack Query for HTTP calls.
- Canvas renderer via Konva or plain Canvas.
- Zod schemas generated or mirrored from backend OpenAPI.
- Vitest and Playwright.

### Artifact Layout

```text
backend/
  app/
    api/
    core/
    sim/
    rl/
    lab/
  policies/
  runs/
  benchmark/
frontend/
  app/
  components/
  lib/
PLAN_CODEX_VERSION.md
```

## 4. Core Technical Decisions

### 4.1 Simulation

Use a deterministic 2D top-down simulator:

- car state: body center `(x, y)`, heading `theta`, velocity `v`, steering
  angle `delta`;
- controls: acceleration and steering-rate;
- center-referenced bicycle model with rear-axle offset;
- passive coast/drag;
- oriented-box collision;
- rectangular static obstacles;
- fixed simulation step, likely `dt = 0.1 s`;
- all units SI: metres, seconds, radians.

Keep simulation pure and separately tested. The API, RL env, replay endpoint,
and frontend visualization should all use the same simulator contract.

### 4.2 Observation

Use an ego-frame observation that supports transfer:

- LIDAR distances, normalized;
- goal position in ego frame;
- goal heading error as sin/cos;
- current velocity;
- current steering angle;
- previous action, because controls are rate-limited;
- rear-axle-to-goal delta and body-center-to-goal delta, because parking
  success depends on body pose while turning behavior depends on axle geometry.

Avoid absolute obstacle coordinates in the policy observation. They make the
policy memorize scenes instead of learning a parking skill.

### 4.3 Action

Default action:

```text
[normalized_acceleration, normalized_steering_rate]
```

Optional later action abstraction:

```text
[target_speed, target_steering_angle]
```

The second form can be easier for RL, but the first is closer to the existing
simulator and manual drive controls.

### 4.4 Termination

Success should require:

- distance to goal below threshold;
- heading error below threshold;
- speed below threshold;
- no collision;
- optionally steering angle near zero for a clean final pose.

Also add:

- collision terminal;
- out-of-bounds terminal;
- timeout truncation;
- no-progress truncation when the agent camps near the goal without improving.

Do not loosen success distance to hide failures.

### 4.5 Reward

Use a reward that makes success unmistakably optimal:

- large terminal success reward;
- large collision penalty;
- small time penalty;
- small control effort penalty;
- potential-based progress terms;
- near-goal alignment potential;
- no positive per-step "being near goal" bonus unless it is proven not to make
  camping profitable.

Every reward change must be accompanied by:

- one unit test for the term;
- one diagnostic rollout against a known failure case;
- benchmark eval before promotion.

## 5. Training Strategy

### 5.1 Policy Families

Train separate policy families before attempting a single general policy:

1. `parallel-family`
2. `perpendicular-family`
3. `reverse-family`
4. `open-goal-family`

Later, distill or fine-tune into a broader goal-conditioned policy.

### 5.2 Curriculum Ladder

Each family should have an explicit ladder.

Parallel:

```text
open corridor
wide parallel slot
medium parallel slot
target parallel slot
tight parallel slot
```

Perpendicular:

```text
open north-facing goal
wide perpendicular slot
medium perpendicular slot
target 2.8 m slot
slot with back wall
```

Reverse-garage:

```text
already aligned reverse entry
offset reverse entry
turn-then-reverse with wide aisle
full reverse-garage
```

Tight-squeeze:

```text
parallel policy warm-start
9 m slot
7.5 m slot
6.2 m target slot
```

### 5.3 Algorithm Order

Use this order for every new maneuver:

1. Train the easiest sibling from scratch.
2. Confirm 100% deterministic and >= 80% stochastic success over 50 episodes.
3. Fine-tune the next harder sibling from the previous champion.
4. Repeat until target geometry.
5. Only then try reward changes.
6. Only use BC if the BC policy passes standalone rollout eval.

### 5.4 Evaluation Gate

A policy can be promoted only if:

- deterministic success >= 90% over 50 episodes;
- stochastic success >= 70% over 50 episodes;
- collision rate <= 5%;
- mean episode length is reasonable for the maneuver;
- diagnostic final states satisfy all success criteria with margin.

For demo-only policies, allow a lower stochastic gate if deterministic replay is
the product path, but mark the artifact clearly.

### 5.5 Run Manifest

Every training run writes:

```json
{
  "run_id": "parallel_warm_easy_parallel_seed42",
  "preset": "parallel",
  "algorithm": "SAC",
  "seed": 42,
  "total_timesteps": 2000000,
  "warm_start": "easy-parallel.zip",
  "reward_version": "potential_v1",
  "curriculum_stage": "target_parallel",
  "git_commit": "...",
  "eval": {
    "det_success": 1.0,
    "stoch_success": 0.92,
    "mean_return": 127.68,
    "mean_length": 128
  }
}
```

Codex should never overwrite a policy artifact without first writing a manifest
and preserving the previous champion.

## 6. Codex Implementation Phases

### Phase 0: Repo Scaffold

Deliverables:

- backend package scaffold;
- frontend scaffold;
- shared README;
- dev commands;
- CI-style test commands;
- formatting and lint config.

Acceptance:

- backend tests run;
- frontend typecheck runs;
- empty app renders.

### Phase 1: Schemas and Deterministic Simulator

Deliverables:

- scene schema;
- car spec schema;
- action schema;
- bicycle model;
- OBB collision;
- lot bounds;
- LIDAR;
- pure replay function.

Tests:

- bicycle straight-line motion;
- bicycle turn radius sanity;
- coast-down behavior;
- collision overlap;
- LIDAR ray distances;
- deterministic replay under seed.

Acceptance:

- manual JSON scene can be replayed headlessly;
- simulator has no frontend dependency.

### Phase 2: Frontend Scene Editor and Manual Drive

Deliverables:

- 2D canvas editor;
- drag ego, goal, and obstacles;
- preset selector;
- manual drive controls;
- LIDAR overlay;
- import/export JSON;
- validation errors.

Acceptance:

- user can construct a scene;
- manual drive posts actions to backend or simulates locally through the same
  schema contract;
- exported scene reloads identically.

### Phase 3: RL Environment and Evaluation Lab

Deliverables:

- Gymnasium env;
- observation/action spaces;
- reward module;
- termination module;
- `train` CLI;
- `evaluate` CLI;
- `diagnose` CLI;
- benchmark scenes;
- run manifests.

Acceptance:

- random policy eval completes;
- a tiny smoke training saves and reloads a policy;
- benchmark eval prints success, collision, timeout, final distance, heading,
  speed, and episode length.

### Phase 4: Easy Policy Families

Deliverables:

- `scene_easy`;
- `easy-parallel`;
- `easy-perpendicular`;
- `easy-reverse-garage`;
- initial trained policies.

Acceptance:

- each easy policy reaches 100% deterministic success over 50 episodes;
- each policy can be replayed in the browser.

### Phase 5: Warm-Start Curriculum

Deliverables:

- policy warm-start support;
- artifact registry;
- curriculum stage definitions;
- `parallel`, `perpendicular`, `tight-squeeze`, and `reverse-garage` fine-tune
  recipes.

Acceptance:

- `parallel` target solved from `easy-parallel`;
- at least one hard backlog scene solved from a sibling policy;
- all failures produce diagnostic summaries, not silent "bad policy" artifacts.

### Phase 6: Teacher and BC Upgrade

Deliverables:

- geometric path planner or scripted teacher;
- trajectory dataset format;
- BC training;
- BC standalone eval gate;
- optional DAgger-style data collection.

Acceptance:

- BC policy can drive at least one hard scene without PPO fine-tuning;
- BC warm-start improves training speed or final success versus no warm-start.

### Phase 7: Live Training and Telemetry

Deliverables:

- run manager;
- one active run at a time;
- WebSocket stream;
- episode metrics;
- sampled trajectories;
- cancellation;
- frontend progress panel.

Acceptance:

- backend event loop remains responsive during training;
- frontend can watch live rollouts;
- completed run can be replayed from saved policy.

### Phase 8: Product Polish

Deliverables:

- policy selector;
- benchmark dashboard;
- trajectory comparison;
- failure reason display;
- docs for adding a preset;
- docs for running a training sweep.

Acceptance:

- a new developer can add a scene, train/evaluate a policy, and expose it in
  the UI by following docs.

## 7. Initial Preset Set

Start with these presets:

1. `scene_easy`: open corridor, no parking geometry.
2. `easy-parallel`: wide parallel slot.
3. `parallel`: realistic but solvable parallel slot.
4. `easy-perpendicular`: wide perpendicular slot.
5. `perpendicular`: target narrow perpendicular slot.
6. `back-in-parallel`: reverse-mandatory parallel slot.
7. `easy-tight-squeeze`: intermediate parallel slot.
8. `tight-squeeze`: target tight slot.
9. `easy-reverse-garage`: aligned reverse-garage.
10. `reverse-garage`: full turn-and-reverse scene.

Do not make `tight-squeeze` or `reverse-garage` first-class success gates until
the easy siblings are solved.

## 8. Commands Codex Should Create

Backend:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy app
uv run python -m app.lab.evaluate --preset parallel --policy policies/parallel.zip --episodes 50
uv run python -m app.lab.train --preset easy-parallel --algo sac --seed 42 --total-timesteps 1000000
uv run python -m app.lab.sweep --recipe recipes/parallel_warm_start.yaml
uv run python -m app.lab.diagnose --preset parallel --policy policies/parallel.zip --episodes 10
```

Frontend:

```bash
npm install
npm run typecheck
npm run lint
npm run test
npm run dev
```

## 9. Files Codex Should Create First

```text
backend/app/core/schemas.py
backend/app/sim/bicycle.py
backend/app/sim/geometry.py
backend/app/sim/lidar.py
backend/app/sim/scene.py
backend/app/sim/replay.py
backend/app/rl/env.py
backend/app/rl/reward.py
backend/app/lab/train.py
backend/app/lab/evaluate.py
backend/app/lab/diagnose.py
backend/app/lab/manifests.py
backend/app/rl/presets.py
frontend/lib/schemas.ts
frontend/lib/presets.ts
frontend/lib/api.ts
frontend/components/editor/SceneCanvas.tsx
frontend/components/editor/Toolbar.tsx
frontend/components/replay/ReplayPanel.tsx
```

## 10. Known Risks and Mitigations

Risk: RL learns to camp near the goal.

Mitigation: potential-based shaping, no-progress truncation, terminal reward
dominance, diagnostics for near-goal timeouts.

Risk: BC fits actions but fails in closed-loop rollout.

Mitigation: standalone BC eval gate before fine-tuning.

Risk: hard scenes need multi-stage maneuvers PPO/SAC does not discover.

Mitigation: easy sibling curriculum, teacher trajectories, planner-generated
data.

Risk: frontend and backend scene definitions drift.

Mitigation: Pydantic schema as source of truth, generated OpenAPI types,
preset parity tests.

Risk: successful policies are overwritten by failed experiments.

Mitigation: immutable run artifacts, champion symlinks or copied promotion,
manifest required before promotion.

Risk: seed variance hides true performance.

Mitigation: seed sweeps, deterministic and stochastic eval, benchmark gates.

## 11. First Codex Task List

1. Scaffold backend and frontend.
2. Implement schemas and pure simulator.
3. Add simulator unit tests.
4. Add preset definitions and parity tests.
5. Implement replay API.
6. Build minimal editor and replay canvas.
7. Implement Gymnasium env.
8. Implement reward v1 with potential-based shaping.
9. Build `evaluate` and `diagnose` CLIs before long training.
10. Train `scene_easy`.
11. Train `easy-parallel`.
12. Fine-tune `parallel` from `easy-parallel`.
13. Add artifact manifests and champion promotion.
14. Only then add live training WebSocket.

## 12. Definition of Done for the Codex Version

The first complete Codex version is done when:

- the frontend can edit and replay scenes;
- backend replay and policy eval use the same simulator;
- `scene_easy`, `easy-parallel`, `parallel`, and one non-parallel family policy
  pass promotion gates;
- every policy artifact has a manifest;
- failed policies show useful diagnostics in the UI or CLI;
- live training is optional, not required for the demo to work.

