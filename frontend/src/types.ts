// Copyright (c) 2026 Athena Decisions Systems SAS.
export interface ObjRef { name: string; word: string | null; }

export interface GameState {
  session_id?: string;
  location: number;
  name: string;
  description: string;
  dark: boolean;
  visible_objects: ObjRef[];
  inventory: ObjRef[];
  exits: string[];
  score: number;
  max_score: number;
  turns: number;
  carrying: number;
  lamp_on: boolean;
  closing: boolean;
  closed: boolean;
  ended: boolean;
}

export interface Scene {
  location: number;
  name?: string;
  mimetype: string;
  cached: boolean;
  prompt: string;
  data_uri: string;
}

export interface MapPayload {
  mermaid: string;
  node_count: number;
  edge_count: number;
  center: number | null;
}
