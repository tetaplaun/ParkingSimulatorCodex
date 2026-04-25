import { useEffect, useMemo, useState } from "react";

import { SceneCanvas } from "./components/editor/SceneCanvas";
import { Toolbar } from "./components/editor/Toolbar";
import { ReplayPanel } from "./components/replay/ReplayPanel";
import { replayBest } from "./lib/api";
import { PRESET_KEYS, buildPreset } from "./lib/presets";
import { buildDemoActions, replayLocal } from "./lib/replay";
import type { ReplaySource } from "./lib/api";
import type { PresetKey, ReplayResult } from "./lib/schemas";

export default function App() {
  const [presetKey, setPresetKey] = useState<PresetKey>("scene_easy");
  const [stepIndex, setStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showLidar, setShowLidar] = useState(false);
  const [policyReplay, setPolicyReplay] = useState<ReplayResult | null>(null);
  const [replaySource, setReplaySource] = useState<"loading" | ReplaySource | "demo script">(
    "loading"
  );
  const scene = useMemo(() => buildPreset(presetKey), [presetKey]);
  const actions = useMemo(() => buildDemoActions(scene), [scene]);
  const scriptedReplay = useMemo(() => replayLocal(scene, actions), [scene, actions]);
  const replay = policyReplay ?? scriptedReplay;
  const maxStep = Math.max(0, replay.steps.length - 1);
  const clampedStep = Math.min(stepIndex, maxStep);
  const canPlay = maxStep > 0;

  useEffect(() => {
    let cancelled = false;
    setPolicyReplay(null);
    setReplaySource("loading");
    replayBest(presetKey)
      .then((result) => {
        if (cancelled) return;
        setPolicyReplay(result?.replay ?? null);
        setReplaySource(result?.source ?? "demo script");
      })
      .catch(() => {
        if (cancelled) return;
        setPolicyReplay(null);
        setReplaySource("demo script");
      });
    return () => {
      cancelled = true;
    };
  }, [presetKey]);

  useEffect(() => {
    setIsPlaying(false);
    setStepIndex((currentStep) => Math.min(currentStep, maxStep));
  }, [maxStep]);

  useEffect(() => {
    if (!isPlaying) return;
    if (!canPlay || clampedStep >= maxStep) {
      setIsPlaying(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setStepIndex((currentStep) => Math.min(currentStep + 1, maxStep));
    }, 55);

    return () => window.clearTimeout(timer);
  }, [canPlay, clampedStep, isPlaying, maxStep]);

  function handlePresetChange(nextPreset: PresetKey) {
    setIsPlaying(false);
    setPresetKey(nextPreset);
    setStepIndex(0);
  }

  function handlePlayPause() {
    if (!canPlay) return;
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    if (clampedStep >= maxStep) {
      setStepIndex(0);
    }
    setIsPlaying(true);
  }

  function handleReset() {
    setIsPlaying(false);
    setStepIndex(0);
  }

  function handleStepChange(nextStep: number) {
    setIsPlaying(false);
    setStepIndex(nextStep);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Scene controls">
        <div>
          <p className="eyebrow">ParkingSimulator Codex</p>
          <h1>Scene Lab</h1>
        </div>
        <Toolbar
          presetKey={presetKey}
          presets={PRESET_KEYS}
          canPlay={canPlay}
          isPlaying={isPlaying}
          showLidar={showLidar}
          onPresetChange={handlePresetChange}
          onPlayPause={handlePlayPause}
          onReset={handleReset}
          onShowLidarChange={setShowLidar}
        />
        <ReplayPanel
          replay={replay}
          replaySource={replaySource}
          scene={scene}
          stepIndex={clampedStep}
        />
      </aside>

      <section className="stage" aria-label="Scene canvas">
        <div className="canvas-frame">
          <SceneCanvas
            scene={scene}
            replay={replay}
            stepIndex={clampedStep}
            showLidar={showLidar}
          />
        </div>
        <div className="timeline">
          <label htmlFor="step-range">Replay step</label>
          <input
            id="step-range"
            type="range"
            min={0}
            max={maxStep}
            value={clampedStep}
            onChange={(event) => handleStepChange(Number(event.target.value))}
          />
          <output>{clampedStep}</output>
        </div>
      </section>
    </main>
  );
}
