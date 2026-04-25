from __future__ import annotations

from app.core.schemas import Action, ParkingScene, ReplayResult, SimStep
from app.sim.bicycle import step_bicycle
from app.sim.lidar import scan_lidar
from app.sim.scene import goal_metrics, has_collision, is_out_of_bounds, is_success


def replay(
    scene: ParkingScene,
    actions: list[Action],
    *,
    include_lidar: bool = False,
) -> ReplayResult:
    state = scene.start
    steps: list[SimStep] = []
    reason = "actions_exhausted"
    terminated = False
    success = False

    for index, action in enumerate(actions[: scene.max_steps], start=1):
        state = step_bicycle(state, action, scene.car_spec, scene.dt)
        collision = has_collision(scene, state)
        out_of_bounds = is_out_of_bounds(scene, state)
        success = is_success(scene, state)

        steps.append(
            SimStep(
                index=index,
                state=state,
                action=action,
                metrics=goal_metrics(scene, state),
                collision=collision,
                out_of_bounds=out_of_bounds,
                success=success,
                lidar_distances=scan_lidar(scene, state) if include_lidar else None,
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

    if not terminated and len(actions) >= scene.max_steps:
        reason = "timeout"

    return ReplayResult(
        scene_id=scene.id,
        steps=steps,
        final_state=state,
        reason=reason,
        success=success,
        terminated=terminated,
    )
