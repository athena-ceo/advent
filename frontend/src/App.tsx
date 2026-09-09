// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useCallback, useEffect, useRef, useState } from "react";
import { api, setAuthToken, type User } from "./api";
import type { GameState, Scene } from "./types";
import { ScenePanel } from "./components/ScenePanel";
import { MapPanel } from "./components/MapPanel";
import { StatusBar } from "./components/StatusBar";
import { Transcript, type Line } from "./components/Transcript";
import { CommandBar } from "./components/CommandBar";
import { InfoModal, type InfoKind } from "./components/InfoModal";
import { AuthModal } from "./components/AuthModal";
import { LeaderboardModal } from "./components/LeaderboardModal";
import { AdminModal } from "./components/AdminModal";

type Mode = "classic" | "guided";

const SESSION_KEY = "advent.session_id";
const LEFT_KEY = "advent.leftFrac";
const MAP_KEY = "advent.showMap";
const STYLE_KEY = "advent.style";

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

  // --- UI layout preferences (persisted) ---
  const [leftFrac, setLeftFrac] = useState(() => {
    const v = parseFloat(localStorage.getItem(LEFT_KEY) ?? "");
    return Number.isFinite(v) && v > 0.2 && v < 0.85 ? v : 0.55;
  });
  const [showMap, setShowMap] = useState(() => localStorage.getItem(MAP_KEY) === "1");
  const [styles, setStyles] = useState<string[]>([]);
  const [style, setStyle] = useState<string>(() => localStorage.getItem(STYLE_KEY) ?? "");
  const [info, setInfo] = useState<InfoKind | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [boardOpen, setBoardOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  // Who am I? (registered account via token, else a guest row)
  useEffect(() => { api.me().then((r) => setUser(r.user)).catch(() => {}); }, []);

  const logout = async () => {
    try { await api.logout(); } catch { /* ignore */ }
    setAuthToken(null);
    setUser(null);
  };

  useEffect(() => { localStorage.setItem(LEFT_KEY, String(leftFrac)); }, [leftFrac]);
  useEffect(() => { localStorage.setItem(MAP_KEY, showMap ? "1" : "0"); }, [showMap]);
  useEffect(() => { if (style) localStorage.setItem(STYLE_KEY, style); }, [style]);

  // Available style libraries (photoreal / fantasy / …) come from the backend.
  useEffect(() => {
    api.styles().then((s) => {
      setStyles(s.styles);
      setStyle((cur) => cur || s.default);
    }).catch(() => { /* styles are best-effort; empty menu just hides it */ });
  }, []);

  const startDrag = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const el = mainRef.current;
    if (!el) return;
    const onMove = (ev: MouseEvent) => {
      const r = el.getBoundingClientRect();
      const frac = (ev.clientX - r.left) / r.width;
      setLeftFrac(Math.min(0.82, Math.max(0.25, frac)));
    };
    const onUp = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }, []);

  const push = (line: Line) => setLines((ls) => [...ls, line]);

  const refreshPanels = useCallback(async (id: string) => {
    setSceneLoading(true);
    try {
      const [sc, mp] = await Promise.all([api.scene(id, style), api.map(id, mapDepth)]);
      setScene(sc);
      setMapCode(mp.mermaid);
    } catch { /* panels are best-effort */ } finally {
      setSceneLoading(false);
    }
  }, [mapDepth, style]);

  // Refetch just the map when the depth control changes.
  useEffect(() => {
    if (!sid) return;
    api.map(sid, mapDepth).then((m) => setMapCode(m.mermaid)).catch(() => {});
  }, [mapDepth, sid]);

  // Re-render the current scene in the chosen style library.
  useEffect(() => {
    if (!sid || !style) return;
    setSceneLoading(true);
    api.scene(sid, style).then(setScene).catch(() => {}).finally(() => setSceneLoading(false));
  }, [style, sid]);

  const newGame = useCallback(async () => {
    setBusy(true);
    try {
      const g = await api.newGame();
      setSid(g.session_id);
      localStorage.setItem(SESSION_KEY, g.session_id);
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

  // On load, reattach to the session from a previous visit (survives reloads);
  // start a fresh game only if there isn't one, or it's gone/ended.
  const boot = useCallback(async () => {
    const saved = localStorage.getItem(SESSION_KEY);
    if (saved) {
      try {
        const st = await api.state(saved);
        if (!st.ended) {
          setSid(saved);
          setState(st);
          try {
            const t = await api.transcript(saved);
            setLines([
              { kind: "system", text: "— resumed your game —" },
              ...t.log.map((e) => ({ kind: e.kind, text: e.text })),
            ]);
          } catch { /* transcript is best-effort */ }
          await refreshPanels(saved);
          return;
        }
      } catch { /* stale/unknown session id -> start fresh */ }
    }
    await newGame();
  }, [newGame, refreshPanels]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void boot();
  }, [boot]);

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
      localStorage.setItem(SESSION_KEY, g.session_id);
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

  const btn = "px-3 py-1 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 disabled:opacity-40";

  return (
    <div className="h-full flex flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b border-cave-600 bg-cave-800">
        <div className="flex items-baseline gap-3">
          <h1 className="font-serif text-lg text-amber-glow">Colossal Cave</h1>
          <span className="text-xs text-cave-300">Adventure · 350 points</span>
          <button onClick={() => setInfo("help")}
            className="text-xs px-2 py-0.5 rounded border border-cave-600 bg-cave-700 hover:border-amber-glow/60">Help</button>
          <button onClick={() => setInfo("about")}
            className="text-xs px-2 py-0.5 rounded border border-cave-600 bg-cave-700 hover:border-amber-glow/60">About</button>
          <button onClick={() => setBoardOpen(true)}
            className="text-xs px-2 py-0.5 rounded border border-cave-600 bg-cave-700 hover:border-amber-glow/60">Scores</button>
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
          {styles.length > 0 && (
            <select value={style} onChange={(e) => setStyle(e.target.value)}
              title="Image style library"
              className="px-2 py-1 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 capitalize">
              {styles.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
          <button onClick={() => setShowMap((v) => !v)}
            className={`px-3 py-1 rounded border ${showMap
              ? "bg-amber-glow text-cave-900 border-amber-glow font-semibold"
              : "bg-cave-700 border-cave-600 hover:border-amber-glow/60"}`}>
            Map
          </button>
          <button onClick={save} disabled={!sid || busy} className={btn}>Save</button>
          <button onClick={restore} disabled={!saveId || busy} className={btn}>Restore</button>
          <button onClick={newGame} disabled={busy} className={btn}>New</button>
          <span className="w-px h-5 bg-cave-600 mx-1" />
          {user?.registered ? (
            <div className="flex items-center gap-1">
              <span className="text-amber-glow font-semibold px-1" title="signed in">{user.name}</span>
              <button onClick={logout} className={btn}>Sign out</button>
            </div>
          ) : (
            <button onClick={() => setAuthOpen(true)} className={btn}>Sign in</button>
          )}
        </div>
      </header>

      <main ref={mainRef} className="flex-1 flex flex-col lg:flex-row gap-3 p-4 overflow-hidden">
        <section style={{ flexBasis: `${leftFrac * 100}%` }}
          className="flex flex-col rounded-lg border border-cave-600 bg-cave-800 overflow-hidden min-h-0 lg:min-w-0">
          <Transcript lines={lines} busy={busy} />
          <CommandBar
            onSend={send}
            disabled={busy || !sid}
            placeholder={mode === "classic" ? "e.g. go west, take lamp, xyzzy" : "tell the game master what you want to do…"}
          />
        </section>

        {/* Draggable divider (desktop only); double-click resets the split. */}
        <div onMouseDown={startDrag} onDoubleClick={() => setLeftFrac(0.55)}
          title="Drag to resize · double-click to reset"
          className="hidden lg:flex shrink-0 w-2 items-center justify-center cursor-col-resize group">
          <div className="w-0.5 h-16 rounded bg-cave-600 group-hover:bg-amber-glow/70" />
        </div>

        <aside className="flex-1 flex flex-col gap-3 min-h-0 min-w-0">
          <ScenePanel scene={scene} loading={sceneLoading}
            dark={!!state?.dark && (state?.location ?? 0) > 0} />
          <div className="shrink-0 flex flex-col gap-3 overflow-y-auto scroll-thin max-h-[55%]">
            <StatusBar state={state} onAction={send} />
            {showMap && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-cave-300 mb-1 px-1">Cave map</div>
                <MapPanel code={mapCode} depth={mapDepth} onDepth={setMapDepth} />
              </div>
            )}
          </div>
        </aside>
      </main>

      {info && <InfoModal kind={info} onClose={() => setInfo(null)} />}
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onAuth={setUser} />}
      {boardOpen && (
        <LeaderboardModal onClose={() => setBoardOpen(false)}
          onAdmin={() => { setBoardOpen(false); setAdminOpen(true); }} />
      )}
      {adminOpen && <AdminModal onClose={() => setAdminOpen(false)} />}
    </div>
  );
}
