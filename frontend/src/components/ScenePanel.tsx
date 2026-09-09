// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { Scene } from "../types";

export function ScenePanel({ scene, loading, dark }: { scene?: Scene; loading: boolean; dark?: boolean }) {
  return (
    <div className="flex flex-col min-h-0 rounded-lg overflow-hidden border border-cave-600 bg-cave-800 shadow-lg">
      <div className="relative flex-1 min-h-0 bg-cave-900 flex items-center justify-center">
        {scene ? (
          <img src={scene.data_uri} alt={scene.name ?? "scene"}
            className="w-full h-full object-contain transition-[filter] duration-700"
            // In a dark room with no light, the player can't see it -- dim the
            // plate heavily and cool it, so the art matches "it is pitch dark".
            style={dark ? { filter: "brightness(0.09) contrast(1.1) saturate(0.5)" } : undefined} />
        ) : (
          <span className="text-cave-300 text-sm">{loading ? "conjuring the scene…" : "no scene"}</span>
        )}
        {dark && scene && (
          <div className="absolute inset-0 flex items-end justify-center pb-4 pointer-events-none">
            <span className="text-cave-300/80 text-xs font-mono tracking-wide">it is pitch dark — you need a light</span>
          </div>
        )}
      </div>
      <div className="shrink-0 px-3 py-2 flex items-center justify-between text-xs border-t border-cave-600">
        <span className="font-serif text-amber-glow/90 truncate">{scene?.name ?? ""}</span>
        {scene && (
          <span className="text-cave-300" title={scene.prompt}>
            {scene.cached ? "cached" : "generated"} · #{scene.location}
          </span>
        )}
      </div>
    </div>
  );
}
