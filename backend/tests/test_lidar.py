from math import isclose

from app.core.schemas import CarState, LidarConfig, ParkingScene, Pose, RectBounds, RectObstacle
from app.sim.lidar import scan_lidar


def test_lidar_reports_front_obstacle_distance() -> None:
    scene = ParkingScene(
        id="lidar",
        name="Lidar",
        bounds=RectBounds(min_x=-10.0, max_x=10.0, min_y=-5.0, max_y=5.0),
        start=CarState(),
        goal=Pose(),
        obstacles=[RectObstacle(id="box", x=5.0, y=0.0, width=1.0, height=2.0)],
        lidar=LidarConfig(rays=3, fov=0.2, max_distance=20.0),
    )

    distances = scan_lidar(scene, CarState(x=0.0, y=0.0, theta=0.0))

    assert isclose(distances[1], 4.5)

