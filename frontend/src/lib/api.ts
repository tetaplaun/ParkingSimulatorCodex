import type { Action, ParkingScene, PresetKey, ReplayResult } from "./schemas";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

export type ReplaySource = "trained policy" | "scripted teacher";

export interface BestReplayResponse {
  source: ReplaySource;
  replay: ReplayResult;
}

export async function fetchPreset(key: PresetKey): Promise<ParkingScene> {
  const response = await fetch(`${API_BASE}/presets/${key}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch preset ${key}: ${response.status}`);
  }
  return response.json() as Promise<ParkingScene>;
}

export async function replayScene(
  scene: ParkingScene,
  actions: Action[],
  includeLidar = false
): Promise<ReplayResult> {
  const response = await fetch(`${API_BASE}/replay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scene, actions, include_lidar: includeLidar })
  });
  if (!response.ok) {
    throw new Error(`Replay failed: ${response.status}`);
  }
  return response.json() as Promise<ReplayResult>;
}

export async function replayPolicy(preset: PresetKey): Promise<ReplayResult | null> {
  const response = await fetch(`${API_BASE}/policies/${preset}/replay`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Policy replay failed: ${response.status}`);
  }
  return response.json() as Promise<ReplayResult>;
}

export async function replayBest(preset: PresetKey): Promise<BestReplayResponse | null> {
  const response = await fetch(`${API_BASE}/replays/${preset}/best`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Replay lookup failed: ${response.status}`);
  }
  const data = (await response.json()) as {
    source: "trained_policy" | "scripted_teacher";
    replay: ReplayResult;
  };
  return {
    source: data.source === "trained_policy" ? "trained policy" : "scripted teacher",
    replay: data.replay
  };
}
