// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { GameState, Scene } from "./types";
import { ScenePanel } from "./components/ScenePanel";
import { MapPanel } from "./components/MapPanel";
import { StatusBar } from "./components/StatusBar";
import { Transcript, type Line } from "./components/Transcript";
import { CommandBar } from "./components/CommandBar";

type Mode = "classic" | "guided";

export default function App() {
  const [mode, setMode] = useState<Mode>("classic");
  const [sid, setSid] = useState<string | null>(null);
  const [state, setState] = useState<GameState>();
  const [scene, setScene] = useState<Scene>();
  const [mapCode, setMapCode] = useState<string>();
  const [lines, setLines] = useState<Line[]>([]);
  const [busy, setBusy] = useState(false);
  const [saveId, setSaveId] = useState<string | null>(null);
  const [sceneLoading, setSceneLoading] = useState(false);
  const [mapDepth, setMapDepth] = useState<number | undefined>(1);
  const started = useRef(false);

  const push = (line: Line) => setLines((ls) => [...ls, line]);

  const refreshPanels = useCallback(async (id: string) => {
    setSceneLoading(true);
    try {
      const [sc, mp] = await Promise.all([api.scene(id), api.map(id, mapDepth)]);
      setScene(sc);
      setMapCode(mp.mermaid);
    } catch { /* panels are best-effort */ } finally {
      setSceneLoading(false);
    }
  }, [mapDepth]);

  // Refetch just the map when the depth control changes.
  useEffect(() => {
    if (!sid) return;
    api.map(sid, mapDepth).then((m) => setMapCode(m.mermaid)).catch(() => {});
  }, [mapDepth, sid]);

  const newGame = useCallback(async () => {
    setBusy(true);
    try {
      const g = await api.newGame();
      setSid(g.session_id);
      setState(g.state);
      setSaveId(null);
      setLines([{ kind: "game", text: g.intro }]);
      await refreshPanels(g.session_id);
    } catch (e) {
      push({ kind: "system", text: `could not start a game: ${e}` });
    } finally {
      setBusy(false);
    }
  }, [refreshPanels]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void newGame();
  }, [newGame]);

  const send = async (text: string) => {
    if (!sid || busy) return;
    push({ kind: "you", text });
    setBusy(true);
    try {
      if (mode === "classic") {
        const r = await api.command(sid, text);
        push({ kind: "game", text: r.output || "(nothing happens)" });
        setState(r.state);
      } else {
        const r = await api.chat(sid, text);
        push({ kind: "game", text: r.reply });
        setState(r.state);
      }
      await refreshPanels(sid);
    } catch (e) {
      push({ kind: "system", text: `${e}` });
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    if (!sid) return;
    try {
      const r = await api.save(sid);
      setSaveId(r.save_id);
      push({ kind: "system", text: "adventure saved." });
    } catch (e) { push({ kind: "system", text: `${e}` }); }
  };

  const restore = async () => {
    if (!saveId) return;
    setBusy(true);
    try {
      const g = await api.restore(saveId);
      setSid(g.session_id);
      setState(g.state);
      push({ kind: "system", text: "restored to the saved point." });
      push({ kind: "game", text: g.intro });
      await refreshPanels(g.session_id);
    } catch (e) {
      push({ kind: "system", text: `${e}` });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b border-cave-600 bg-cave-800">
        <div className="flex items-baseline gap-3">
          <h1 className="font-serif text-lg text-amber-glow">Colossal Cave</h1>
          <span className="text-xs text-cave-600">Adventure · 350 points</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <div className="flex rounded overflow-hidden border border-cave-600">
            {(["classic", "guided"] as Mode[]).map((m) => (
              <button key={m} onClick={() => setMode(m)}
                className={`px-3 py-1 ${mode === m ? "bg-amber-glow text-cave-900 font-semibold" : "bg-cave-700 hover:bg-cave-600"}`}>
                {m === "classic" ? "Classic" : "Guided"}
              </button>
            ))}
          </div>
          <button onClick={save} disabled={!sid || busy}
            className="px-3 py-1 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 disabled:opacity-40">Save</button>
          <button onClick={restore} disabled={!saveId || busy}
            className="px-3 py-1 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 disabled:opacity-40">Restore</button>
          <button onClick={newGame} disabled={busy}
            className="px-3 py-1 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 disabled:opacity-40">New</button>
        </div>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-4 p-4 overflow-hidden">
        <section className="flex flex-col rounded-lg border border-cave-600 bg-cave-800 overflow-hidden min-h-0">
          <Transcript lines={lines} />
          <CommandBar
            onSend={send}
            disabled={busy || !sid}
            placeholder={mode === "classic" ? "e.g. go west, take lamp, xyzzy" : "tell the game master what you want to do…"}
          />
        </section>

        <aside className="flex flex-col gap-4 overflow-y-auto scroll-thin min-h-0">
          <ScenePanel scene={scene} loading={sceneLoading} />
          <StatusBar state={state} onAction={send} />
          <div>
            <div className="text-[10px] uppercase tracking-wider text-cave-600 mb-1 px-1">Cave map</div>
            <MapPanel code={mapCode} depth={mapDepth} onDepth={setMapDepth} />
          </div>
        </aside>
      </main>
    </div>
  );
}
