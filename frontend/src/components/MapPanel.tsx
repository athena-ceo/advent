// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import panzoom, { type PanZoom } from "panzoom";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  flowchart: { curve: "basis", nodeSpacing: 28, rankSpacing: 44 },
});

let counter = 0;

function MapCanvas({ code, className }: { code?: string; className?: string }) {
  const host = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!code || !host.current) return;
    let cancelled = false;
    let instance: PanZoom | null = null;
    const id = `cavemap-${counter++}`;
    mermaid.render(id, code).then(({ svg }) => {
      if (cancelled || !host.current) return;
      host.current.innerHTML = svg;
      setError(null);
      const el = host.current.querySelector("svg") as SVGSVGElement | null;
      if (!el) return;
      // Fit the whole subgraph into the panel (centered), then let the user
      // scroll-zoom / drag to explore. The amber node is the current room.
      el.removeAttribute("width");
      el.removeAttribute("height");
      el.setAttribute("preserveAspectRatio", "xMidYMid meet");
      el.style.width = "100%";
      el.style.height = "auto";
      el.style.maxHeight = "100%";
      instance = panzoom(el, { maxZoom: 12, minZoom: 0.3, bounds: false, zoomDoubleClickSpeed: 1 });
    }).catch((e) => { if (!cancelled) setError(String(e)); });
    return () => { cancelled = true; instance?.dispose(); };
  }, [code]);

  return error
    ? <div className="text-red-400 text-xs p-2">{error}</div>
    : <div ref={host} className={`w-full h-full overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing ${className ?? ""}`} />;
}

const DEPTHS: { label: string; depth: number | undefined }[] = [
  { label: "Here", depth: 1 },
  { label: "Nearby", depth: 2 },
  { label: "Area", depth: 3 },
  { label: "All", depth: undefined },
];

export function MapPanel({ code, depth, onDepth }: {
  code?: string; depth: number | undefined;
  onDepth: (d: number | undefined) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const toolbar = (
    <div className="flex items-center gap-1 text-[11px]">
      {DEPTHS.map((d) => (
        <button key={d.label} onClick={() => onDepth(d.depth)}
          className={`px-2 py-0.5 rounded border ${depth === d.depth
            ? "bg-amber-glow text-cave-900 border-amber-glow font-semibold"
            : "bg-cave-700 border-cave-600 hover:border-amber-glow/60"}`}>
          {d.label}
        </button>
      ))}
    </div>
  );

  return (
    <>
      <div className="rounded-lg border border-cave-600 bg-cave-800">
        <div className="flex items-center justify-between px-2 py-1.5 border-b border-cave-600">
          {toolbar}
          <button onClick={() => setExpanded(true)}
            className="text-[11px] px-2 py-0.5 rounded border bg-cave-700 border-cave-600 hover:border-amber-glow/60">
            ⤢ Expand
          </button>
        </div>
        <div className="h-[320px]"><MapCanvas code={code} /></div>
        <div className="px-2 py-1 text-[10px] text-cave-600">scroll to zoom · drag to pan</div>
      </div>

      {expanded && (
        <div className="fixed inset-0 z-50 bg-cave-900/95 flex flex-col p-4" onClick={() => setExpanded(false)}>
          <div className="flex items-center justify-between mb-2" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2">
              <span className="font-serif text-amber-glow">Cave map</span>
              {toolbar}
            </div>
            <button onClick={() => setExpanded(false)}
              className="px-3 py-1 rounded border bg-cave-700 border-cave-600 hover:border-amber-glow/60 text-sm">
              Close ✕
            </button>
          </div>
          <div className="flex-1 rounded-lg border border-cave-600 bg-cave-800 overflow-hidden"
            onClick={(e) => e.stopPropagation()}>
            <MapCanvas code={code} />
          </div>
        </div>
      )}
    </>
  );
}
