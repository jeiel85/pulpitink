import { invoke } from "@tauri-apps/api/core";

export async function sidecarSync(args: string[]): Promise<string> {
  return invoke<string>("run_pulpit_ink_sidecar_sync", { args });
}

export async function sidecarSpawn(args: string[]): Promise<string> {
  return invoke<string>("run_pulpit_ink_sidecar", { args });
}

export async function sidecarSyncJson<T>(args: string[]): Promise<T> {
  const raw = await sidecarSync(args);
  return JSON.parse(raw) as T;
}
