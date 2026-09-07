// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { GameState, MapPayload, Scene } from "./types";

const API = import.meta.env.VITE_API_BASE ?? "/api";

async function jfetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface TurnResult { output: string; state: GameState; ended: boolean; }
export interface NewGameResult { session_id: string; intro: string; state: GameState; }
export interface ChatResult { reply: string; state: GameState; }

export const api = {
  newGame: (seed?: number) =>
    jfetch<NewGameResult>("/games", { method: "POST", body: JSON.stringify({ seed }) }),
  command: (sid: string, command: string) =>
    jfetch<TurnResult>(`/games/${sid}/command`, { method: "POST", body: JSON.stringify({ command }) }),
  state: (sid: string) => jfetch<GameState>(`/games/${sid}/state`),
  transcript: (sid: string) =>
    jfetch<{ session_id: string; transcript: string[] }>(`/games/${sid}/transcript`),
  scene: (sid: string) => jfetch<Scene>(`/games/${sid}/scene`),
  map: (sid: string, depth?: number) =>
    jfetch<MapPayload>(`/games/${sid}/map${depth != null ? `?depth=${depth}` : ""}`),
  save: (sid: string) => jfetch<{ save_id: string }>(`/games/${sid}/save`, { method: "POST" }),
  restore: (saveId: string) =>
    jfetch<NewGameResult>("/restore", { method: "POST", body: JSON.stringify({ save_id: saveId }) }),
  chat: (sid: string, message: string) =>
    jfetch<ChatResult>(`/games/${sid}/chat`, { method: "POST", body: JSON.stringify({ message }) }),
};
