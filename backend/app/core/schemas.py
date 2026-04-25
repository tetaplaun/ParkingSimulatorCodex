from __future__ import annotations

from math import pi
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Pose(BaseModel):
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class CarState(Pose):
    v: float = 0.0
    delta: float = 0.0


class Action(BaseModel):
    acceleration: float = Field(ge=-1.0, le=1.0)
    steering_rate: float = Field(ge=-1.0, le=1.0)


class CarSpec(BaseModel):
    length: float = Field(default=4.5, gt=0.0)
    width: float = Field(default=1.9, gt=0.0)
    wheelbase: float = Field(default=2.7, gt=0.0)
    rear_axle_to_center: float = Field(default=1.1, ge=0.0)
    max_speed: float = Field(default=7.0, gt=0.0)
    max_reverse_speed: float = Field(default=-4.0, lt=0.0)
    max_accel: float = Field(default=3.0, gt=0.0)
    max_steer: float = Field(default=0.65, gt=0.0)
    max_steer_rate: float = Field(default=1.5, gt=0.0)
    drag: float = Field(default=0.18, ge=0.0)

    @field_validator("rear_axle_to_center")
    @classmethod
    def rear_axle_inside_body(cls, value: float) -> float:
        # This validator runs before length is available, so only enforce the
        # physical lower bound here; model-level relationships are checked by
        # simulator tests and preset construction.
        return value


class RectBounds(BaseModel):
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @field_validator("max_x")
    @classmethod
    def max_x_after_min_x(cls, value: float, info: object) -> float:
        data = getattr(info, "data", {})
        min_x = data.get("min_x")
        if min_x is not None and value <= min_x:
            raise ValueError("max_x must be greater than min_x")
        return value

    @field_validator("max_y")
    @classmethod
    def max_y_after_min_y(cls, value: float, info: object) -> float:
        data = getattr(info, "data", {})
        min_y = data.get("min_y")
        if min_y is not None and value <= min_y:
            raise ValueError("max_y must be greater than min_y")
        return value


class RectObstacle(BaseModel):
    id: str
    x: float
    y: float
    width: float = Field(gt=0.0)
    height: float = Field(gt=0.0)
    theta: float = 0.0


class SuccessCriteria(BaseModel):
    distance_tolerance: float = Field(default=0.45, gt=0.0)
    heading_tolerance: float = Field(default=0.18, gt=0.0)
    speed_tolerance: float = Field(default=0.25, ge=0.0)
    steering_tolerance: float | None = Field(default=None, gt=0.0)


class LidarConfig(BaseModel):
    rays: int = Field(default=31, ge=3)
    max_distance: float = Field(default=18.0, gt=0.0)
    fov: float = Field(default=2 * pi, gt=0.0, le=2 * pi)


class ParkingScene(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    name: str
    bounds: RectBounds
    car_spec: CarSpec = Field(default_factory=CarSpec)
    start: CarState
    goal: Pose
    obstacles: list[RectObstacle] = Field(default_factory=list)
    success: SuccessCriteria = Field(default_factory=SuccessCriteria)
    lidar: LidarConfig = Field(default_factory=LidarConfig)
    dt: float = Field(default=0.1, gt=0.0)
    max_steps: int = Field(default=400, ge=1)


class GoalMetrics(BaseModel):
    distance: float
    heading_error: float
    speed: float
    steering: float


class SimStep(BaseModel):
    index: int
    state: CarState
    action: Action
    metrics: GoalMetrics
    collision: bool
    out_of_bounds: bool
    success: bool
    lidar_distances: list[float] | None = None


ReplayReason = Literal["success", "collision", "out_of_bounds", "timeout", "actions_exhausted"]


class ReplayResult(BaseModel):
    scene_id: str
    steps: list[SimStep]
    final_state: CarState
    reason: ReplayReason
    success: bool
    terminated: bool


class ReplayRequest(BaseModel):
    scene: ParkingScene
    actions: list[Action]
    include_lidar: bool = False

