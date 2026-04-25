from __future__ import annotations

from math import pi

from app.core.schemas import CarState, ParkingScene, Pose, RectBounds, RectObstacle, SuccessCriteria

PRESET_KEYS = (
    "scene_easy",
    "easy-parallel",
    "parallel",
    "easy-perpendicular",
    "perpendicular",
    "back-in-parallel",
    "easy-tight-squeeze",
    "tight-squeeze",
    "easy-reverse-garage",
    "reverse-garage",
)


def _parallel_slot(scene_id: str, name: str, slot_length: float, start_x: float) -> ParkingScene:
    parked_length = 4.8
    gap = slot_length / 2.0 + parked_length / 2.0
    return ParkingScene(
        id=scene_id,
        name=name,
        bounds=RectBounds(min_x=-8.0, max_x=14.0, min_y=-5.0, max_y=6.0),
        start=CarState(x=start_x, y=-2.0, theta=0.0, v=0.0, delta=0.0),
        goal=Pose(x=2.0, y=1.2, theta=0.0),
        obstacles=[
            RectObstacle(id="parked_front", x=2.0 + gap, y=1.2, width=parked_length, height=2.1),
            RectObstacle(id="parked_rear", x=2.0 - gap, y=1.2, width=parked_length, height=2.1),
            RectObstacle(id="curb", x=2.0, y=2.75, width=20.0, height=0.25),
        ],
        success=SuccessCriteria(
            distance_tolerance=0.5,
            heading_tolerance=0.2,
            speed_tolerance=0.25,
        ),
        max_steps=450,
    )


def _perpendicular(scene_id: str, name: str, slot_width: float) -> ParkingScene:
    half_gap = slot_width / 2.0 + 1.2
    return ParkingScene(
        id=scene_id,
        name=name,
        bounds=RectBounds(min_x=-7.0, max_x=9.0, min_y=-6.0, max_y=8.0),
        start=CarState(x=-3.5, y=-2.5, theta=0.0, v=0.0, delta=0.0),
        goal=Pose(x=1.0, y=3.2, theta=pi / 2.0),
        obstacles=[
            RectObstacle(id="left_parked", x=1.0 - half_gap, y=3.2, width=2.1, height=4.8),
            RectObstacle(id="right_parked", x=1.0 + half_gap, y=3.2, width=2.1, height=4.8),
            RectObstacle(id="back_wall", x=1.0, y=5.8, width=9.0, height=0.25),
        ],
        success=SuccessCriteria(
            distance_tolerance=0.5,
            heading_tolerance=0.2,
            speed_tolerance=0.25,
        ),
        max_steps=450,
    )


def _reverse_garage(scene_id: str, name: str, aligned: bool) -> ParkingScene:
    start = (
        CarState(x=0.2, y=1.2, theta=-pi / 2.0, v=0.0, delta=0.0)
        if aligned
        else CarState(x=-4.0, y=-1.5, theta=0.0, v=0.0, delta=0.0)
    )
    return ParkingScene(
        id=scene_id,
        name=name,
        bounds=RectBounds(min_x=-8.0, max_x=8.0, min_y=-6.0, max_y=8.0),
        start=start,
        goal=Pose(x=0.0, y=3.8, theta=-pi / 2.0),
        obstacles=[
            RectObstacle(id="left_wall", x=-1.8, y=3.8, width=0.25, height=5.2),
            RectObstacle(id="right_wall", x=1.8, y=3.8, width=0.25, height=5.2),
            RectObstacle(id="back_wall", x=0.0, y=6.3, width=3.8, height=0.25),
        ],
        success=SuccessCriteria(
            distance_tolerance=0.45,
            heading_tolerance=0.18,
            speed_tolerance=0.2,
        ),
        max_steps=520,
    )


def build_preset(key: str) -> ParkingScene:
    match key:
        case "scene_easy":
            return ParkingScene(
                id="scene_easy",
                name="Open corridor",
                bounds=RectBounds(min_x=-8.0, max_x=12.0, min_y=-5.0, max_y=5.0),
                start=CarState(x=-5.0, y=0.0, theta=0.0, v=0.0, delta=0.0),
                goal=Pose(x=5.0, y=0.0, theta=0.0),
                success=SuccessCriteria(
                    distance_tolerance=0.5,
                    heading_tolerance=0.2,
                    speed_tolerance=0.25,
                ),
                max_steps=300,
            )
        case "easy-parallel":
            return _parallel_slot(key, "Easy parallel", slot_length=9.0, start_x=-4.0)
        case "parallel":
            return _parallel_slot(key, "Parallel", slot_length=6.8, start_x=-5.0)
        case "back-in-parallel":
            return _parallel_slot(key, "Back-in parallel", slot_length=8.0, start_x=8.0)
        case "easy-tight-squeeze":
            return _parallel_slot(key, "Easy tight squeeze", slot_length=7.5, start_x=-5.0)
        case "tight-squeeze":
            return _parallel_slot(key, "Tight squeeze", slot_length=6.2, start_x=-5.5)
        case "easy-perpendicular":
            return _perpendicular(key, "Easy perpendicular", slot_width=3.8)
        case "perpendicular":
            return _perpendicular(key, "Perpendicular", slot_width=2.8)
        case "easy-reverse-garage":
            return _reverse_garage(key, "Easy reverse garage", aligned=True)
        case "reverse-garage":
            return _reverse_garage(key, "Reverse garage", aligned=False)
        case _:
            raise KeyError(f"Unknown preset: {key}")
