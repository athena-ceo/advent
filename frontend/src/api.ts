// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { GameState, MapPayload, Scene } from "./types";

const API = import.meta.env.VITE_API_BASE ?? "/api";

// --- identity ---------------------------------------------------------------
// A stable anonymous guest id (per browser) plus, once signed in, a bearer
// token. Both ride along as headers so the backend can attribute play.
const PID_KEY = "advent.player_id";
const TOKEN_KEY = "advent.token";

function guestId(): string {
  let id = localStorage.getItem(PID_KEY);
  if (!id) {
    id = (crypto.randomUUID?.() ?? Math.random().toString(36).slice(2)).replace(/-/g, "").slice(0, 12);
    localStorage.setItem(PID_KEY, id);
  }
  return id;
}
export function authToken(): string | null { return localStorage.getItem(TOKEN_KEY); }
export function setAuthToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY);
}

function headers(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", "X-Advent-Player": guestId() };
  const t = authToken();
  if (t) h["X-Advent-Token"] = t;
  return { ...h, ...extra };
}

async function jfetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, { ...init, headers: headers(init?.headers as Record<string, string>) });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface TurnResult { output: string; state: GameState; ended: boolean; }
export interface User { id: string; name: string | null; is_admin: boolean; registered: boolean; }
export interface NewGameResult { session_id: string; intro: string; state: GameState; player?: User | null; }
export interface ChatResult { reply: string; state: GameState; }
export interface LeaderRow { name: string; score: number; turns: number; ended: number; registered: number; }
export interface Metrics {
  players_total: number; registered_total: number; games_total: number;
  players_active: number; games_active: number; completions: number;
  top_score: number; active_window_min: number;
}
export interface AdminUser { id: string; name: string; is_admin: number; games: number; best: number; last_seen: number; created: number; }
export interface AdminGame { id: string; player: string; score: number; turns: number; location: number; ended: number; updated: number; }

export const api = {
  newGame: (seed?: number) =>
    jfetch<NewGameResult>("/games", { method: "POST", body: JSON.stringify({ seed }) }),
  command: (sid: string, command: string) =>
    jfetch<TurnResult>(`/games/${sid}/command`, { method: "POST", body: JSON.stringify({ command }) }),
  state: (sid: string) => jfetch<GameState>(`/games/${sid}/state`),
  transcript: (sid: string) =>
    jfetch<{ session_id: string; log: { kind: "you" | "game"; text: string }[] }>(
      `/games/${sid}/transcript`),
  scene: (sid: string, style?: string) =>
    jfetch<Scene>(`/games/${sid}/scene${style ? `?style=${encodeURIComponent(style)}` : ""}`),
  styles: () => jfetch<{ styles: string[]; default: string }>("/styles"),
  map: (sid: string, depth?: number) =>
    jfetch<MapPayload>(`/games/${sid}/map${depth != null ? `?depth=${depth}` : ""}`),
  save: (sid: string) => jfetch<{ save_id: string }>(`/games/${sid}/save`, { method: "POST" }),
  restore: (saveId: string) =>
    jfetch<NewGameResult>("/restore", { method: "POST", body: JSON.stringify({ save_id: saveId }) }),
  chat: (sid: string, message: string) =>
    jfetch<ChatResult>(`/games/${sid}/chat`, { method: "POST", body: JSON.stringify({ message }) }),

  // accounts
  me: () => jfetch<{ user: User | null }>("/auth/me"),
  register: (name: string, password: string) =>
    jfetch<{ user: User; token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ name, password }) }),
  login: (name: string, password: string) =>
    jfetch<{ user: User; token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ name, password }) }),
  logout: () => jfetch<{ ok: boolean }>("/auth/logout", { method: "POST" }),

  // tracking
  leaderboard: (limit = 20) => jfetch<{ entries: LeaderRow[] }>(`/leaderboard?limit=${limit}`),
  metrics: () => jfetch<Metrics>("/metrics"),

  // admin (password sent per call, not stored)
  adminUsers: (pw: string) => jfetch<{ users: AdminUser[] }>("/admin/users", { headers: { "X-Advent-Admin": pw } }),
  adminGames: (pw: string) => jfetch<{ games: AdminGame[] }>("/admin/games", { headers: { "X-Advent-Admin": pw } }),
  adminReset: (pw: string) => jfetch<{ removed: number }>("/admin/reset-leaderboard", { method: "POST", headers: { "X-Advent-Admin": pw } }),
  adminDeleteUser: (pw: string, player_id: string) =>
    jfetch<{ ok: boolean }>("/admin/delete-user", { method: "POST", headers: { "X-Advent-Admin": pw }, body: JSON.stringify({ player_id }) }),
};
