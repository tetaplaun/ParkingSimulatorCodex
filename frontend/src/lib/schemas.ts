export type PresetKey =
  | "scene_easy"
  | "easy-parallel"
  | "parallel"
  | "easy-perpendicular"
  | "perpendicular"
  | "back-in-parallel"
  | "easy-tight-squeeze"
  | "tight-squeeze"
  | "easy-reverse-garage"
  | "reverse-garage";

export interface Pose {
  x: number;
  y: number;
  theta: number;
}

export interface CarState extends Pose {
  v: number;
  delta: number;
}

export interface Action {
  acceleration: number;
  steering_rate: number;
}

export interface CarSpec {
  length: number;
  width: number;
  wheelbase: number;
  rear_axle_to_center: number;
  max_speed: number;
  max_reverse_speed: number;
  max_accel: number;
  max_steer: number;
  max_steer_rate: number;
  drag: number;
}

export interface RectBounds {
  min_x: number;
  max_x: number;
  min_y: number;
  max_y: number;
}

export interface RectObstacle {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  theta: number;
}

export interface SuccessCriteria {
  distance_tolerance: number;
  heading_tolerance: number;
  speed_tolerance: number;
  steering_tolerance?: number | null;
}

export interface LidarConfig {
  rays: number;
  max_distance: number;
  fov: number;
}

export interface ParkingScene {
  id: PresetKey | string;
  name: string;
  bounds: RectBounds;
  car_spec: CarSpec;
  start: CarState;
  goal: Pose;
  obstacles: RectObstacle[];
  success: SuccessCriteria;
  lidar: LidarConfig;
  dt: number;
  max_steps: number;
}

export interface GoalMetrics {
  distance: number;
  heading_error: number;
  speed: number;
  steering: number;
}

export interface SimStep {
  index: number;
  state: CarState;
  action: Action;
  metrics: GoalMetrics;
  collision: boolean;
  out_of_bounds: boolean;
  success: boolean;
  lidar_distances?: number[] | null;
}

export interface ReplayResult {
  scene_id: string;
  steps: SimStep[];
  final_state: CarState;
  reason: "success" | "collision" | "out_of_bounds" | "timeout" | "actions_exhausted";
  success: boolean;
  terminated: boolean;
}

export interface TrainingAttempt {
  index: number;
  score: number;
  best: boolean;
  replay: ReplayResult;
}

export interface TrainingStatus {
  run_id: string;
  preset_key: string;
  running: boolean;
  completed: boolean;
  attempts: number;
  max_attempts: number;
  successes: number;
  best_score: number | null;
  best_replay: ReplayResult | null;
  recent_attempts: TrainingAttempt[];
}
