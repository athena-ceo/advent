// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect } from "react";

export function Modal({ title, onClose, children, wide }: {
  title: string; onClose: () => void; children: React.ReactNode; wide?: boolean;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 bg-cave-900/95 flex items-center justify-center p-4" onClick={onClose}>
      <div className={`w-full ${wide ? "max-w-3xl" : "max-w-md"} max-h-[85vh] overflow-y-auto scroll-thin rounded-lg border border-cave-600 bg-cave-800 shadow-2xl`}
        onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 flex items-center justify-between px-5 py-3 border-b border-cave-600 bg-cave-800">
          <h2 className="font-serif text-lg text-amber-glow">{title}</h2>
          <button onClick={onClose}
            className="px-3 py-1 rounded border bg-cave-700 border-cave-600 hover:border-amber-glow/60 text-sm">Close ✕</button>
        </div>
        <div className="px-5 py-4 text-[13px] leading-relaxed text-cave-100 space-y-4">{children}</div>
      </div>
    </div>
  );
}

export const field =
  "w-full bg-cave-900 border border-cave-600 rounded px-3 py-2 outline-none focus:border-amber-glow/60";
export const primaryBtn =
  "px-4 py-1.5 rounded bg-amber-glow text-cave-900 font-semibold disabled:opacity-40";
export const plainBtn =
  "px-3 py-1.5 rounded border bg-cave-700 border-cave-600 hover:border-amber-glow/60 disabled:opacity-40";
