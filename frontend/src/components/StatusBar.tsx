// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { GameState, ObjRef } from "../types";

function Pill({ label, onClick, title }: { label: string; onClick?: () => void; title?: string }) {
  const base = "text-xs px-2 py-0.5 rounded border transition-colors";
  if (!onClick) {
    return <span className={`${base} bg-cave-700 border-cave-600 text-cave-200/80`}>{label}</span>;
  }
  return (
    <button onClick={onClick} title={title}
      className={`${base} bg-cave-700 border-cave-600 hover:border-amber-glow hover:text-amber-glow`}>
      {label}
    </button>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-cave-300 mb-1">{label}</div>
      <div className="flex flex-wrap gap-1">{children}</div>
    </div>
  );
}

export function StatusBar({ state, onAction }: { state?: GameState; onAction: (cmd: string) => void }) {
  if (!state) return null;
  const objPill = (o: ObjRef, verb: string) => (
    <Pill key={o.name} label={o.name}
      onClick={o.word ? () => onAction(`${verb} ${o.word}`) : undefined}
      title={o.word ? `${verb} ${o.word}` : undefined} />
  );
  return (
    <div className="rounded-lg border border-cave-600 bg-cave-800 p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-serif text-amber-glow">{state.name}</span>
        <span className="text-xs text-cave-300">room {state.location}</span>
      </div>
      {state.description && (
        <p className="text-[13px] leading-relaxed whitespace-pre-wrap font-mono text-cave-200/90">
          {state.description}
        </p>
      )}
      <div className="flex gap-4 text-sm">
        <div><span className="text-cave-300">score </span><b>{state.score}</b><span className="text-cave-300">/{state.max_score}</span></div>
        <div><span className="text-cave-300">turns </span><b>{state.turns}</b></div>
        <div><span className="text-cave-300">lamp </span><b className={state.lamp_on ? "text-amber-glow" : ""}>{state.lamp_on ? "on" : "off"}</b></div>
      </div>
      {state.visible_objects.length > 0 && (
        <Row label="You see (take)">{state.visible_objects.map((o) => objPill(o, "take"))}</Row>
      )}
      {state.inventory.length > 0 && (
        <Row label="Carrying (drop)">{state.inventory.map((o) => objPill(o, "drop"))}</Row>
      )}
      {state.exits.length > 0 && (
        <Row label="Exits (go)">
          {state.exits.map((x) => <Pill key={x} label={x} onClick={() => onAction(x)} title={`go ${x}`} />)}
        </Row>
      )}
      {state.ended && <div className="text-amber-glow text-sm font-serif">— the adventure has ended —</div>}
    </div>
  );
}
