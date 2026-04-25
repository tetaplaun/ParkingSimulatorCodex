import type { ParkingScene, ReplayResult } from "../../lib/schemas";

interface ReplayPanelProps {
  scene: ParkingScene;
  replay: ReplayResult;
  replaySource: "loading" | "trained policy" | "scripted teacher" | "demo script";
  stepIndex: number;
}

function formatNumber(value: number, fractionDigits = 2): string {
  return value.toFixed(fractionDigits);
}

export function ReplayPanel({ scene, replay, replaySource, stepIndex }: ReplayPanelProps) {
  const step = replay.steps[stepIndex];
  const metrics = step?.metrics;
  const status = step?.success
    ? "success"
    : step?.out_of_bounds
      ? "out_of_bounds"
      : step?.collision
        ? "collision"
        : "running";

  return (
    <section className="metrics-panel" aria-label="Replay metrics">
      <div>
        <span>Scene</span>
        <strong>{scene.name}</strong>
      </div>
      <div>
        <span>Status</span>
        <strong>{status}</strong>
      </div>
      <div>
        <span>Source</span>
        <strong>{replaySource}</strong>
      </div>
      <div>
        <span>Steps</span>
        <strong>{replay.steps.length}</strong>
      </div>
      {metrics ? (
        <>
          <div>
            <span>Distance</span>
            <strong>{formatNumber(metrics.distance)} m</strong>
          </div>
          <div>
            <span>Heading Error</span>
            <strong>{formatNumber(metrics.heading_error)} rad</strong>
          </div>
          <div>
            <span>Speed</span>
            <strong>{formatNumber(metrics.speed)} m/s</strong>
          </div>
        </>
      ) : null}
    </section>
  );
}
