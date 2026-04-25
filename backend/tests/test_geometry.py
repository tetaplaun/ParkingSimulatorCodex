from app.sim.geometry import OrientedBox, obb_intersects


def test_obb_collision_overlap() -> None:
    left = OrientedBox(x=0.0, y=0.0, length=4.0, width=2.0, theta=0.0)
    right = OrientedBox(x=1.5, y=0.0, length=4.0, width=2.0, theta=0.2)

    assert obb_intersects(left, right)


def test_obb_collision_separated() -> None:
    left = OrientedBox(x=0.0, y=0.0, length=4.0, width=2.0, theta=0.0)
    right = OrientedBox(x=6.1, y=0.0, length=2.0, width=2.0, theta=0.0)

    assert not obb_intersects(left, right)

