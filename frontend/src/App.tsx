import { useEffect, useMemo, useState } from "react";

import { SceneCanvas } from "./components/editor/SceneCanvas";
import { Toolbar } from "./components/editor/Toolbar";
import { ReplayPanel } from "./components/replay/ReplayPanel";
import { fetchTrainingStatus, replayBest, startTraining, stopTraining } from "./lib/api";
import { PRESET_KEYS, buildPreset } from "./lib/presets";
import { buildDemoActions, replayLocal } from "./lib/replay";
import type { ReplaySource } from "./lib/api";
import type { PresetKey, ReplayResult, TrainingStatus } from "./lib/schemas";

export default function App() {
  const [presetKey, setPresetKey] = useState<PresetKey>("scene_easy");
  const [stepIndex, setStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showLidar, setShowLidar] = useState(false);
  const [policyReplay, setPolicyReplay] = useState<ReplayResult | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [trainingRunId, setTrainingRunId] = useState<string | null>(null);
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
  const isTraining = Boolean(trainingStatus?.running);

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

  useEffect(() => {
    if (!trainingRunId) return;

    const activeRunId = trainingRunId;
    let cancelled = false;
    let timer: number | undefined;

    async function pollTraining() {
      try {
        const status = await fetchTrainingStatus(activeRunId);
        if (cancelled) return;
        setTrainingStatus(status);
        if (status.running) {
          timer = window.setTimeout(pollTraining, 360);
        }
      } catch {
        if (!cancelled) {
          setTrainingRunId(null);
        }
      }
    }

    timer = window.setTimeout(pollTraining, 180);
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [trainingRunId]);

  function handlePresetChange(nextPreset: PresetKey) {
    if (trainingStatus?.running) {
      void stopTraining(trainingStatus.run_id).catch(() => undefined);
    }
    setTrainingStatus(null);
    setTrainingRunId(null);
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

  async function handleTrainToggle() {
    setIsPlaying(false);
    if (trainingStatus?.running) {
      const status = await stopTraining(trainingStatus.run_id);
      setTrainingStatus(status);
      setTrainingRunId(null);
      return;
    }

    setStepIndex(0);
    const status = await startTraining(presetKey);
    setTrainingStatus(status);
    setTrainingRunId(status.run_id);
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
          isTraining={isTraining}
          showLidar={showLidar}
          onPresetChange={handlePresetChange}
          onPlayPause={handlePlayPause}
          onReset={handleReset}
          onTrainToggle={() => void handleTrainToggle()}
          onShowLidarChange={setShowLidar}
        />
        <ReplayPanel
          replay={replay}
          replaySource={replaySource}
          scene={scene}
          stepIndex={clampedStep}
          trainingStatus={trainingStatus}
        />
      </aside>

      <section className="stage" aria-label="Scene canvas">
        <div className="canvas-frame">
          <SceneCanvas
            scene={scene}
            replay={replay}
            stepIndex={clampedStep}
            showLidar={showLidar}
            trainingAttempts={trainingStatus?.recent_attempts ?? []}
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
