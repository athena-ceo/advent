// Copyright (c) 2026 Athena Decisions Systems SAS.
import type { Scene } from "../types";

export function ScenePanel({ scene, loading }: { scene?: Scene; loading: boolean }) {
  return (
    <div className="rounded-lg overflow-hidden border border-cave-600 bg-cave-800 shadow-lg">
      <div className="aspect-[16/10] bg-cave-900 flex items-center justify-center">
        {scene ? (
          <img src={scene.data_uri} alt={scene.name ?? "scene"} className="w-full h-full object-cover" />
        ) : (
          <span className="text-cave-600 text-sm">{loading ? "conjuring the scene…" : "no scene"}</span>
        )}
      </div>
      <div className="px-3 py-2 flex items-center justify-between text-xs">
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
