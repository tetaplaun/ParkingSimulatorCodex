from app.sim.live_training import get_training_status, start_training


def test_live_training_generates_attempt_trails() -> None:
    status = start_training("easy-tight-squeeze", max_attempts=6, seed=7)

    status = get_training_status(status.run_id, advance_by=6)

    assert status is not None
    assert status.completed
    assert status.attempts == 6
    assert status.successes >= 1
    assert status.best_replay is not None
    assert status.recent_attempts
    assert all(attempt.replay.steps for attempt in status.recent_attempts)
