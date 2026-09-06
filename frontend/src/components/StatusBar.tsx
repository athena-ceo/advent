// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { GameState } from "../types";

function Chips({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-cave-600 mb-1">{label}</div>
      <div className="flex flex-wrap gap-1">
        {items.length ? items.map((i) => (
          <span key={i} className="text-xs px-2 py-0.5 rounded bg-cave-700 border border-cave-600">{i}</span>
        )) : <span className="text-xs text-cave-600">—</span>}
      </div>
    </div>
  );
}

export function StatusBar({ state }: { state?: GameState }) {
  if (!state) return null;
  return (
    <div className="rounded-lg border border-cave-600 bg-cave-800 p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-serif text-amber-glow">{state.name}</span>
        <span className="text-xs text-cave-600">room {state.location}</span>
      </div>
      <div className="flex gap-4 text-sm">
        <div><span className="text-cave-600">score </span><b>{state.score}</b><span className="text-cave-600">/{state.max_score}</span></div>
        <div><span className="text-cave-600">turns </span><b>{state.turns}</b></div>
        <div><span className="text-cave-600">lamp </span><b className={state.lamp_on ? "text-amber-glow" : ""}>{state.lamp_on ? "on" : "off"}</b></div>
      </div>
      <Chips label="You see" items={state.visible_objects} />
      <Chips label="Carrying" items={state.inventory} />
      <Chips label="Exits" items={state.exits} />
      {state.ended && <div className="text-amber-glow text-sm font-serif">— the adventure has ended —</div>}
    </div>
  );
}
