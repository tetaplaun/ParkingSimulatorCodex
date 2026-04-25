import type { CarState, ParkingScene, Pose, PresetKey, RectBounds, RectObstacle } from "./schemas";

export const PRESET_KEYS: PresetKey[] = [
  "scene_easy",
  "easy-parallel",
  "parallel",
  "easy-perpendicular",
  "perpendicular",
  "back-in-parallel",
  "easy-tight-squeeze",
  "tight-squeeze",
  "easy-reverse-garage",
  "reverse-garage"
];

const BASE_CAR = {
  length: 4.5,
  width: 1.9,
  wheelbase: 2.7,
  rear_axle_to_center: 1.1,
  max_speed: 7.0,
  max_reverse_speed: -4.0,
  max_accel: 3.0,
  max_steer: 0.65,
  max_steer_rate: 1.5,
  drag: 0.18
};

const BASE_SUCCESS = {
  distance_tolerance: 0.45,
  heading_tolerance: 0.18,
  speed_tolerance: 0.25,
  steering_tolerance: null
};

const BASE_LIDAR = {
  rays: 31,
  max_distance: 18,
  fov: 2 * Math.PI
};

function scene(params: {
  id: PresetKey;
  name: string;
  bounds: RectBounds;
  start: CarState;
  goal: Pose;
  obstacles?: RectObstacle[];
  max_steps?: number;
}): ParkingScene {
  return {
    id: params.id,
    name: params.name,
    bounds: params.bounds,
    car_spec: { ...BASE_CAR },
    start: params.start,
    goal: params.goal,
    obstacles: params.obstacles ?? [],
    success: { ...BASE_SUCCESS, distance_tolerance: 0.5, heading_tolerance: 0.2 },
    lidar: { ...BASE_LIDAR },
    dt: 0.1,
    max_steps: params.max_steps ?? 400
  };
}

function parallelSlot(id: PresetKey, name: string, slotLength: number, startX: number): ParkingScene {
  const parkedLength = 4.8;
  const gap = slotLength / 2 + parkedLength / 2;
  return scene({
    id,
    name,
    bounds: { min_x: -8, max_x: 14, min_y: -5, max_y: 6 },
    start: { x: startX, y: -2, theta: 0, v: 0, delta: 0 },
    goal: { x: 2, y: 1.2, theta: 0 },
    obstacles: [
      { id: "parked_front", x: 2 + gap, y: 1.2, width: parkedLength, height: 2.1, theta: 0 },
      { id: "parked_rear", x: 2 - gap, y: 1.2, width: parkedLength, height: 2.1, theta: 0 },
      { id: "curb", x: 2, y: 2.75, width: 20, height: 0.25, theta: 0 }
    ],
    max_steps: 450
  });
}

function perpendicular(id: PresetKey, name: string, slotWidth: number): ParkingScene {
  const halfGap = slotWidth / 2 + 1.2;
  return scene({
    id,
    name,
    bounds: { min_x: -7, max_x: 9, min_y: -6, max_y: 8 },
    start: { x: -3.5, y: -2.5, theta: 0, v: 0, delta: 0 },
    goal: { x: 1, y: 3.2, theta: Math.PI / 2 },
    obstacles: [
      { id: "left_parked", x: 1 - halfGap, y: 3.2, width: 2.1, height: 4.8, theta: 0 },
      { id: "right_parked", x: 1 + halfGap, y: 3.2, width: 2.1, height: 4.8, theta: 0 },
      { id: "back_wall", x: 1, y: 5.8, width: 9, height: 0.25, theta: 0 }
    ],
    max_steps: 450
  });
}

function reverseGarage(id: PresetKey, name: string, aligned: boolean): ParkingScene {
  return scene({
    id,
    name,
    bounds: { min_x: -8, max_x: 8, min_y: -6, max_y: 8 },
    start: aligned
      ? { x: 0.2, y: 1.2, theta: -Math.PI / 2, v: 0, delta: 0 }
      : { x: -4, y: -1.5, theta: 0, v: 0, delta: 0 },
    goal: { x: 0, y: 3.8, theta: -Math.PI / 2 },
    obstacles: [
      { id: "left_wall", x: -1.8, y: 3.8, width: 0.25, height: 5.2, theta: 0 },
      { id: "right_wall", x: 1.8, y: 3.8, width: 0.25, height: 5.2, theta: 0 },
      { id: "back_wall", x: 0, y: 6.3, width: 3.8, height: 0.25, theta: 0 }
    ],
    max_steps: 520
  });
}

export function buildPreset(key: PresetKey): ParkingScene {
  switch (key) {
    case "scene_easy":
      return scene({
        id: "scene_easy",
        name: "Open corridor",
        bounds: { min_x: -8, max_x: 12, min_y: -5, max_y: 5 },
        start: { x: -5, y: 0, theta: 0, v: 0, delta: 0 },
        goal: { x: 5, y: 0, theta: 0 },
        max_steps: 300
      });
    case "easy-parallel":
      return parallelSlot(key, "Easy parallel", 9, -4);
    case "parallel":
      return parallelSlot(key, "Parallel", 6.8, -5);
    case "back-in-parallel":
      return parallelSlot(key, "Back-in parallel", 8, 8);
    case "easy-tight-squeeze":
      return parallelSlot(key, "Easy tight squeeze", 7.5, -5);
    case "tight-squeeze":
      return parallelSlot(key, "Tight squeeze", 6.2, -5.5);
    case "easy-perpendicular":
      return perpendicular(key, "Easy perpendicular", 3.8);
    case "perpendicular":
      return perpendicular(key, "Perpendicular", 2.8);
    case "easy-reverse-garage":
      return reverseGarage(key, "Easy reverse garage", true);
    case "reverse-garage":
      return reverseGarage(key, "Reverse garage", false);
  }
}
