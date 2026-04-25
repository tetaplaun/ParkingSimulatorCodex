from math import pi

from app.core.schemas import Action, CarSpec, CarState
from app.sim.bicycle import step_bicycle


def test_bicycle_straight_line_motion() -> None:
    spec = CarSpec(drag=0.0)
    state = CarState(x=0.0, y=0.0, theta=0.0, v=2.0, delta=0.0)

    next_state = step_bicycle(state, Action(acceleration=0.0, steering_rate=0.0), spec, 1.0)

    assert next_state.x == 2.0
    assert next_state.y == 0.0
    assert next_state.theta == 0.0
    assert next_state.v == 2.0


def test_bicycle_turns_toward_positive_steering() -> None:
    spec = CarSpec(drag=0.0, max_steer_rate=10.0)
    state = CarState(x=0.0, y=0.0, theta=0.0, v=2.0, delta=0.0)

    next_state = step_bicycle(state, Action(acceleration=0.0, steering_rate=1.0), spec, 0.1)

    assert 0.0 < next_state.theta < pi / 2.0
    assert next_state.y > 0.0


def test_bicycle_coasts_down_with_drag() -> None:
    spec = CarSpec(drag=0.5)
    state = CarState(x=0.0, y=0.0, theta=0.0, v=4.0, delta=0.0)

    next_state = step_bicycle(state, Action(acceleration=0.0, steering_rate=0.0), spec, 1.0)

    assert next_state.v == 2.0

