import { describe, expect, it } from "vitest";

import { PRESET_KEYS, buildPreset } from "./presets";
import { buildDemoActions, replayLocal } from "./replay";

describe("presets", () => {
  it("builds every configured preset", () => {
    const scenes = PRESET_KEYS.map((key) => buildPreset(key));

    expect(scenes.map((scene) => scene.id)).toEqual(PRESET_KEYS);
  });

  it("keeps the reverse garage fallback demo inside the garage wall", () => {
    const scene = buildPreset("easy-reverse-garage");
    const replay = replayLocal(scene, buildDemoActions(scene));

    expect(replay.final_state.y).toBeLessThan(6.0);
  });
});
