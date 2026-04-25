import type { Action, CarState, GoalMetrics, ParkingScene, PresetKey, ReplayResult } from "./schemas";

function clip(value: number, lower: number, upper: number): number {
  return Math.min(Math.max(value, lower), upper);
}

export function normalizeAngle(angle: number): number {
  let normalized = angle;
  while (normalized <= -Math.PI) normalized += 2 * Math.PI;
  while (normalized > Math.PI) normalized -= 2 * Math.PI;
  return normalized;
}

export function stepBicycle(state: CarState, action: Action, scene: ParkingScene): CarState {
  const spec = scene.car_spec;
  const dt = scene.dt;
  let v = state.v + action.acceleration * spec.max_accel * dt;
  if (action.acceleration === 0 && spec.drag > 0) {
    v *= Math.max(0, 1 - spec.drag * dt);
  }
  v = clip(v, spec.max_reverse_speed, spec.max_speed);

  const delta = clip(
    state.delta + action.steering_rate * spec.max_steer_rate * dt,
    -spec.max_steer,
    spec.max_steer
  );
  const thetaDot = (v / spec.wheelbase) * Math.tan(delta);
  const theta = normalizeAngle(state.theta + thetaDot * dt);

  const rearX = state.x - spec.rear_axle_to_center * Math.cos(state.theta);
  const rearY = state.y - spec.rear_axle_to_center * Math.sin(state.theta);
  const nextRearX = rearX + v * Math.cos(state.theta) * dt;
  const nextRearY = rearY + v * Math.sin(state.theta) * dt;

  return {
    x: nextRearX + spec.rear_axle_to_center * Math.cos(theta),
    y: nextRearY + spec.rear_axle_to_center * Math.sin(theta),
    theta,
    v,
    delta
  };
}

function metrics(scene: ParkingScene, state: CarState): GoalMetrics {
  return {
    distance: Math.hypot(state.x - scene.goal.x, state.y - scene.goal.y),
    heading_error: Math.abs(normalizeAngle(state.theta - scene.goal.theta)),
    speed: Math.abs(state.v),
    steering: Math.abs(state.delta)
  };
}

function inBounds(scene: ParkingScene, state: CarState): boolean {
  const bounds = scene.bounds;
  return (
    state.x >= bounds.min_x &&
    state.x <= bounds.max_x &&
    state.y >= bounds.min_y &&
    state.y <= bounds.max_y
  );
}

function reachedGoal(scene: ParkingScene, state: CarState): boolean {
  const current = metrics(scene, state);
  return (
    current.distance <= scene.success.distance_tolerance &&
    current.heading_error <= scene.success.heading_tolerance &&
    current.speed <= scene.success.speed_tolerance
  );
}

export function replayLocal(scene: ParkingScene, actions: Action[]): ReplayResult {
  let state = scene.start;
  const steps = [];
  let reason: ReplayResult["reason"] = "actions_exhausted";
  let terminated = false;
  let success = false;

  for (const [index, action] of actions.slice(0, scene.max_steps).entries()) {
    state = stepBicycle(state, action, scene);
    const outOfBounds = !inBounds(scene, state);
    success = reachedGoal(scene, state);
    steps.push({
      index: index + 1,
      state,
      action,
      metrics: metrics(scene, state),
      collision: false,
      out_of_bounds: outOfBounds,
      success,
      lidar_distances: null
    });

    if (success) {
      reason = "success";
      terminated = true;
      break;
    }
    if (outOfBounds) {
      reason = "out_of_bounds";
      terminated = true;
      break;
    }
  }

  const finalStep = steps.at(-1);
  const finalState = finalStep?.state ?? scene.start;
  if (!terminated && actions.length >= scene.max_steps) {
    reason = "timeout";
  }

  return {
    scene_id: scene.id,
    steps,
    final_state: finalState,
    reason,
    success,
    terminated
  };
}

function buildOpenCorridorActions(scene: ParkingScene): Action[] {
  let state = scene.start;
  const actions: Action[] = [];
  for (let index = 0; index < scene.max_steps; index += 1) {
    const distance = scene.goal.x - state.x;
    const targetSpeed = Math.min(
      2.6,
      Math.sqrt(Math.max(0, 2 * 1.2 * Math.max(0, distance - 0.25)))
    );
    const acceleration = clip(
      (targetSpeed - state.v) / (scene.car_spec.max_accel * scene.dt),
      -0.8,
      0.45
    );
    const action = { acceleration, steering_rate: 0 };
    actions.push(action);
    state = stepBicycle(state, action, scene);
    if (reachedGoal(scene, state)) break;
  }
  return actions;
}

function buildReverseGarageActions(scene: ParkingScene): Action[] {
  let state = scene.start;
  const actions: Action[] = [];
  for (let index = 0; index < scene.max_steps; index += 1) {
    const distance = scene.goal.y - state.y;
    const targetReverseSpeed = -Math.min(
      1.2,
      Math.sqrt(Math.max(0, 2 * 0.9 * Math.max(0, distance - 0.25)))
    );
    const acceleration = clip(
      (targetReverseSpeed - state.v) / (scene.car_spec.max_accel * scene.dt),
      -0.5,
      0.4
    );
    const action = { acceleration, steering_rate: 0 };
    actions.push(action);
    state = stepBicycle(state, action, scene);
    if (reachedGoal(scene, state)) break;
  }
  return actions;
}

export function buildDemoActions(scene: ParkingScene): Action[] {
  switch (scene.id) {
    case "scene_easy":
      return buildOpenCorridorActions(scene);
    case "easy-reverse-garage":
      return buildReverseGarageActions(scene);
    default:
      return [
        ...Array.from({ length: 25 }, () => ({ acceleration: 0.25, steering_rate: 0.8 })),
        ...Array.from({ length: 35 }, () => ({ acceleration: 0.1, steering_rate: -0.8 })),
        ...Array.from({ length: 40 }, () => ({ acceleration: -0.2, steering_rate: 0 })),
        ...Array.from({ length: 35 }, () => ({ acceleration: 0, steering_rate: 0 }))
      ];
  }
}
