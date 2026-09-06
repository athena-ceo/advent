// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect, useRef } from "react";

export interface Line { kind: "game" | "you" | "system"; text: string; }

export function Transcript({ lines }: { lines: Line[] }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [lines]);
  return (
    <div className="flex-1 overflow-y-auto scroll-thin px-4 py-3 space-y-2 font-mono text-[13px] leading-relaxed">
      {lines.map((l, i) => (
        <div key={i} className={
          l.kind === "you" ? "text-amber-glow" :
          l.kind === "system" ? "text-cave-600 italic" : "text-[#e8e0d0] whitespace-pre-wrap"
        }>
          {l.kind === "you" ? `> ${l.text}` : l.text}
        </div>
      ))}
      <div ref={end} />
    </div>
  );
}
