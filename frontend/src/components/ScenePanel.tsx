// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { Scene } from "../types";

export function ScenePanel({ scene, loading }: { scene?: Scene; loading: boolean }) {
  return (
    <div className="flex flex-col min-h-0 rounded-lg overflow-hidden border border-cave-600 bg-cave-800 shadow-lg">
      <div className="flex-1 min-h-0 bg-cave-900 flex items-center justify-center">
        {scene ? (
          <img src={scene.data_uri} alt={scene.name ?? "scene"} className="w-full h-full object-contain" />
        ) : (
          <span className="text-cave-600 text-sm">{loading ? "conjuring the scene…" : "no scene"}</span>
        )}
      </div>
      <div className="shrink-0 px-3 py-2 flex items-center justify-between text-xs border-t border-cave-600">
        <span className="font-serif text-amber-glow/90 truncate">{scene?.name ?? ""}</span>
        {scene && (
          <span className="text-cave-600" title={scene.prompt}>
            {scene.cached ? "cached" : "generated"} · #{scene.location}
          </span>
        )}
      </div>
    </div>
  );
}
