from app.core.schemas import Action
from app.rl.presets import build_preset
from app.sim.bicycle import step_bicycle
from app.sim.replay import replay
from app.sim.scripted import scripted_replay


def test_replay_is_deterministic() -> None:
    scene = build_preset("scene_easy")
    actions = [Action(acceleration=0.2, steering_rate=0.0) for _ in range(20)]

    left = replay(scene, actions)
    right = replay(scene, actions)

    assert left.final_state == right.final_state
    assert left.steps == right.steps


def test_replay_can_report_lidar() -> None:
    scene = build_preset("easy-parallel")
    result = replay(scene, [Action(acceleration=0.0, steering_rate=0.0)], include_lidar=True)

    assert result.steps[0].lidar_distances is not None
    assert len(result.steps[0].lidar_distances) == scene.lidar.rays


def test_easy_parallel_scripted_replay_succeeds_without_collision() -> None:
    scene = build_preset("easy-parallel")

    result = scripted_replay("easy-parallel", scene)

    assert result.success
    assert result.reason == "success"
    assert result.final_state.v <= scene.success.speed_tolerance
    assert abs(result.final_state.delta) <= 0.15
    assert not any(step.collision for step in result.steps)
    assert not any(step.out_of_bounds for step in result.steps)


def test_easy_tight_squeeze_scripted_replay_succeeds_without_collision() -> None:
    scene = build_preset("easy-tight-squeeze")

    result = scripted_replay("easy-tight-squeeze", scene)

    assert result.success
    assert result.reason == "success"
    assert not any(step.collision for step in result.steps)
    assert not any(step.out_of_bounds for step in result.steps)


def test_easy_parallel_scripted_replay_uses_bicycle_dynamics() -> None:
    scene = build_preset("easy-parallel")

    result = scripted_replay("easy-parallel", scene)

    state = scene.start
    for step in result.steps:
        state = step_bicycle(state, step.action, scene.car_spec, scene.dt)
        assert step.state == state
