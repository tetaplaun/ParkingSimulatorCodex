from app.rl.presets import PRESET_KEYS, build_preset


def test_all_presets_build() -> None:
    scenes = [build_preset(key) for key in PRESET_KEYS]

    assert [scene.id for scene in scenes] == list(PRESET_KEYS)

