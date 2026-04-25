from app.core.schemas import Action
from app.rl.presets import build_preset
from app.rl.reward import compute_reward
from app.sim.bicycle import step_bicycle


def test_progress_reward_is_better_than_reversing_away() -> None:
    scene = build_preset("scene_easy")
    forward = Action(acceleration=0.3, steering_rate=0.0)
    backward = Action(acceleration=-0.3, steering_rate=0.0)

    forward_state = step_bicycle(scene.start, forward, scene.car_spec, scene.dt)
    backward_state = step_bicycle(scene.start, backward, scene.car_spec, scene.dt)

    forward_reward = compute_reward(
        scene,
        scene.start,
        forward_state,
        forward,
        collision=False,
        out_of_bounds=False,
        success=False,
    )
    backward_reward = compute_reward(
        scene,
        scene.start,
        backward_state,
        backward,
        collision=False,
        out_of_bounds=False,
        success=False,
    )

    assert forward_reward.total > backward_reward.total

