import type { PresetKey } from "../../lib/schemas";

interface ToolbarProps {
  presetKey: PresetKey;
  presets: PresetKey[];
  canPlay: boolean;
  isPlaying: boolean;
  isTraining: boolean;
  showLidar: boolean;
  onPresetChange: (preset: PresetKey) => void;
  onPlayPause: () => void;
  onReset: () => void;
  onTrainToggle: () => void;
  onShowLidarChange: (show: boolean) => void;
}

export function Toolbar({
  presetKey,
  presets,
  canPlay,
  isPlaying,
  isTraining,
  showLidar,
  onPresetChange,
  onPlayPause,
  onReset,
  onTrainToggle,
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
