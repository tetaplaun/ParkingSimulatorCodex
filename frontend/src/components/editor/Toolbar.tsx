import type { PresetKey } from "../../lib/schemas";

interface ToolbarProps {
  presetKey: PresetKey;
  presets: PresetKey[];
  canPlay: boolean;
  isPlaying: boolean;
  isTraining: boolean;
  showLidar: boolean;
  trainingMaxAttempts: string;
  onPresetChange: (preset: PresetKey) => void;
  onPlayPause: () => void;
  onReset: () => void;
  onTrainToggle: () => void;
  onTrainingMaxAttemptsChange: (maxAttempts: string) => void;
  onTrainingMaxAttemptsBlur: () => void;
  onShowLidarChange: (show: boolean) => void;
}

export function Toolbar({
  presetKey,
  presets,
  canPlay,
  isPlaying,
  isTraining,
  showLidar,
  trainingMaxAttempts,
  onPresetChange,
  onPlayPause,
  onReset,
  onTrainToggle,
  onTrainingMaxAttemptsChange,
  onTrainingMaxAttemptsBlur,
  onShowLidarChange
}: ToolbarProps) {
  return (
    <div className="toolbar">
      <label className="field">
        <span>Preset</span>
        <select value={presetKey} onChange={(event) => onPresetChange(event.target.value as PresetKey)}>
          {presets.map((preset) => (
            <option key={preset} value={preset}>
              {preset}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Max attempts</span>
        <input
          type="number"
          min={4}
          max={2000}
          step={1}
          value={trainingMaxAttempts}
          disabled={isTraining}
          onBlur={onTrainingMaxAttemptsBlur}
          onChange={(event) => onTrainingMaxAttemptsChange(event.target.value)}
        />
      </label>

      <div className="button-row" aria-label="Replay controls">
        <button type="button" onClick={onReset} title="Reset replay">
          Reset
        </button>
        <button
          type="button"
          onClick={onPlayPause}
          disabled={!canPlay}
          aria-pressed={isPlaying}
          title={isPlaying ? "Pause replay" : "Play replay"}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          onClick={onTrainToggle}
          aria-pressed={isTraining}
          title={isTraining ? "Stop live training" : "Live train this scene"}
        >
          {isTraining ? "Stop" : "Train"}
        </button>
      </div>

      <label className="toggle">
        <input
          type="checkbox"
          checked={showLidar}
          onChange={(event) => onShowLidarChange(event.target.checked)}
        />
        <span>LIDAR</span>
      </label>
    </div>
  );
}
