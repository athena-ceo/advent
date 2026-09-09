// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect, useRef } from "react";

export interface Line { kind: "game" | "you" | "system"; text: string; }

function Thinking() {
  return (
    <div className="flex items-center gap-1.5 text-amber-glow/80" aria-label="thinking">
      <span className="text-cave-300 mr-1">the game master is thinking</span>
      {[0, 1, 2].map((i) => (
        <span key={i} className="inline-block w-1.5 h-1.5 rounded-full bg-amber-glow animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }} />
      ))}
    </div>
  );
}

export function Transcript({ lines, busy }: { lines: Line[]; busy?: boolean }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [lines, busy]);
  return (
    <div className="flex-1 overflow-y-auto scroll-thin px-4 py-3 space-y-2 font-mono text-[13px] leading-relaxed">
      {lines.map((l, i) => (
        <div key={i} className={
          l.kind === "you" ? "text-amber-glow" :
          l.kind === "system" ? "text-cave-300 italic" : "text-[#e8e0d0] whitespace-pre-wrap"
        }>
          {l.kind === "you" ? `> ${l.text}` : l.text}
        </div>
      ))}
      {busy && <Thinking />}
      <div ref={end} />
    </div>
  );
}
