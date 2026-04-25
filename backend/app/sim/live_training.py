from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from math import atan2, hypot, sqrt
from threading import Lock
from uuid import uuid4

from app.core.schemas import (
    Action,
    GoalMetrics,
    ParkingScene,
    ReplayResult,
    TrainingAttempt,
    TrainingStatus,
)
from app.rl.presets import build_preset
from app.sim.bicycle import step_bicycle
from app.sim.geometry import normalize_angle
from app.sim.replay import replay
from app.sim.scripted import has_scripted_replay, scripted_replay

RECENT_ATTEMPT_LIMIT = 24


@dataclass
class TrainingSession:
    run_id: str
    preset_key: str
    scene: ParkingScene
    base_actions: list[Action]
    max_attempts: int
    rng: random.Random
    running: bool = True
    completed: bool = False
    attempts: list[TrainingAttempt] = field(default_factory=list)
    successes: int = 0
    best_score: float | None = None
    best_replay: ReplayResult | None = None


_sessions: dict[str, TrainingSession] = {}
_sessions_lock = Lock()


def start_training(
    preset_key: str,
    *,
    max_attempts: int = 72,
    seed: int | None = None,
) -> TrainingStatus:
    scene = build_preset(preset_key)
    run_id = uuid4().hex[:12]
    session = TrainingSession(
        run_id=run_id,
        preset_key=preset_key,
        scene=scene,
        base_actions=_base_actions(preset_key, scene),
        max_attempts=max(1, max_attempts),
        rng=random.Random(seed if seed is not None else int(time.time() * 1000)),
    )

    with _sessions_lock:
        _sessions[run_id] = session
        return _snapshot(session)


def get_training_status(run_id: str, *, advance_by: int = 0) -> TrainingStatus | None:
    with _sessions_lock:
        session = _sessions.get(run_id)
        if session is None:
            return None
        _advance(session, advance_by)
        return _snapshot(session)


def stop_training(run_id: str) -> TrainingStatus | None:
    with _sessions_lock:
        session = _sessions.get(run_id)
        if session is None:
            return None
        session.running = False
        session.completed = True
        return _snapshot(session)


def _advance(session: TrainingSession, attempt_count: int) -> None:
    if not session.running or session.completed:
        return

    for _ in range(max(0, attempt_count)):
        if len(session.attempts) >= session.max_attempts:
            session.running = False
            session.completed = True
            break

        attempt_number = len(session.attempts) + 1
        result = replay(session.scene, _candidate_actions(session, attempt_number))
        score = _score(result)
        is_best = session.best_score is None or score < session.best_score
        if is_best:
            session.best_score = score
            session.best_replay = result
        if result.success:
            session.successes += 1

        session.attempts.append(
            TrainingAttempt(
                index=attempt_number,
                score=score,
                best=is_best,
                replay=result,
            )
        )

    if len(session.attempts) >= session.max_attempts:
        session.running = False
        session.completed = True


def _snapshot(session: TrainingSession) -> TrainingStatus:
    return TrainingStatus(
        run_id=session.run_id,
        preset_key=session.preset_key,
        running=session.running,
        completed=session.completed,
        attempts=len(session.attempts),
        max_attempts=session.max_attempts,
        successes=session.successes,
        best_score=session.best_score,
        best_replay=session.best_replay,
        recent_attempts=session.attempts[-RECENT_ATTEMPT_LIMIT:],
    )


def _base_actions(preset_key: str, scene: ParkingScene) -> list[Action]:
    if has_scripted_replay(preset_key):
        return [step.action for step in scripted_replay(preset_key, scene).steps]
    return _goal_seeking_actions(scene)


def _goal_seeking_actions(scene: ParkingScene) -> list[Action]:
    state = scene.start
    actions: list[Action] = []
    for _ in range(scene.max_steps):
        distance = hypot(scene.goal.x - state.x, scene.goal.y - state.y)
        target_heading = atan2(scene.goal.y - state.y, scene.goal.x - state.x)
        heading_error = normalize_angle(target_heading - state.theta)
        target_speed = min(2.4, sqrt(max(0.0, 1.6 * max(0.0, distance - 0.35))))
        acceleration = _clip(
            (target_speed - state.v) / (scene.car_spec.max_accel * scene.dt),
            -0.7,
            0.5,
        )
        steering_rate = _clip(heading_error * 2.8 - state.delta * 1.6, -1.0, 1.0)
        action = Action(acceleration=acceleration, steering_rate=steering_rate)
        actions.append(action)
        state = step_bicycle(state, action, scene.car_spec, scene.dt)
    return actions


def _candidate_actions(session: TrainingSession, attempt_number: int) -> list[Action]:
    if attempt_number >= session.max_attempts - 1:
        return session.base_actions

    progress = min(1.0, attempt_number / max(1.0, session.max_attempts - 2.0))
    base_weight = 0.12 + progress * 0.88
    explore_weight = 1.0 - base_weight
    noise_scale = 0.62 * (1.0 - progress)
    actions: list[Action] = []

    for action in session.base_actions:
        acceleration = (
            action.acceleration * base_weight
            + session.rng.uniform(-0.75, 0.75) * explore_weight
            + session.rng.gauss(0.0, 0.18 * noise_scale)
        )
        steering_rate = (
            action.steering_rate * base_weight
            + session.rng.uniform(-1.0, 1.0) * explore_weight
            + session.rng.gauss(0.0, noise_scale)
        )
        actions.append(
            Action(
                acceleration=_clip(acceleration, -1.0, 1.0),
                steering_rate=_clip(steering_rate, -1.0, 1.0),
            )
        )

    return actions


def _score(result: ReplayResult) -> float:
    metrics = goal_metrics_from_replay(result)
    score = metrics.distance + metrics.heading_error * 2.0 + metrics.speed * 0.35
    if result.reason == "collision":
        score += 60.0
    elif result.reason == "out_of_bounds":
        score += 75.0
    elif result.reason == "timeout":
        score += 15.0
    if result.success:
        score -= 100.0
    return score


def goal_metrics_from_replay(result: ReplayResult) -> GoalMetrics:
    if result.steps:
        return result.steps[-1].metrics
    raise ValueError("Cannot score a replay without steps")


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)
