// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  flowchart: { curve: "basis", nodeSpacing: 30, rankSpacing: 40 },
});

let counter = 0;

export function MapPanel({ code }: { code?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!code || !ref.current) return;
    let cancelled = false;
    const id = `cavemap-${counter++}`;
    mermaid
      .render(id, code)
      .then(({ svg }) => { if (!cancelled && ref.current) { ref.current.innerHTML = svg; setError(null); } })
      .catch((e) => { if (!cancelled) setError(String(e)); });
    return () => { cancelled = true; };
  }, [code]);

  return (
    <div className="rounded-lg border border-cave-600 bg-cave-800 p-2 overflow-auto scroll-thin max-h-[320px]">
      {error ? (
        <div className="text-red-400 text-xs">{error}</div>
      ) : (
        <div ref={ref} className="[&_svg]:max-w-none flex justify-center" />
      )}
    </div>
  );
}
