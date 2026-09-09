// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect, useState } from "react";
import { api, type LeaderRow, type Metrics } from "../api";
import { Modal } from "./Modal";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex flex-col items-center px-3 py-1.5 rounded bg-cave-900 border border-cave-600 min-w-[72px]">
      <span className="text-amber-glow font-semibold">{value}</span>
      <span className="text-[10px] uppercase tracking-wider text-cave-300">{label}</span>
    </div>
  );
}

export function LeaderboardModal({ onClose, onAdmin }: { onClose: () => void; onAdmin: () => void }) {
  const [rows, setRows] = useState<LeaderRow[]>([]);
  const [m, setM] = useState<Metrics | null>(null);

  useEffect(() => {
    let live = true;
    const load = () => {
      api.leaderboard(20).then((r) => live && setRows(r.entries)).catch(() => {});
      api.metrics().then((x) => live && setM(x)).catch(() => {});
    };
    load();
    const t = setInterval(load, 20000);  // keep the "online" counts fresh
    return () => { live = false; clearInterval(t); };
  }, []);

  return (
    <Modal title="Leaderboard" onClose={onClose} wide>
      {m && (
        <div className="flex flex-wrap gap-2">
          <Stat label={`online (${m.active_window_min}m)`} value={m.players_active} />
          <Stat label="playing now" value={m.games_active} />
          <Stat label="players" value={m.players_total} />
          <Stat label="games" value={m.games_total} />
          <Stat label="finished" value={m.completions} />
          <Stat label="top score" value={m.top_score} />
        </div>
      )}
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="text-[10px] uppercase tracking-wider text-cave-300">
            <th className="py-1 w-8">#</th><th className="py-1">Player</th>
            <th className="py-1 text-right">Score</th><th className="py-1 text-right">Turns</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-cave-700">
              <td className="py-1 text-cave-300">{i + 1}</td>
              <td className="py-1">
                <span className={r.registered ? "text-cave-100" : "text-cave-300 italic"}>{r.name}</span>
                {r.ended ? <span className="ml-2 text-[10px] text-amber-glow/80">finished</span> : null}
              </td>
              <td className="py-1 text-right font-semibold text-amber-glow">{r.score}</td>
              <td className="py-1 text-right text-cave-300">{r.turns}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><td colSpan={4} className="py-4 text-center text-cave-300">
              No scores yet — be the first to find some treasure.</td></tr>
          )}
        </tbody>
      </table>
      <div className="flex justify-end">
        <button onClick={onAdmin} className="text-[11px] text-cave-300 hover:text-amber-glow underline">
          Admin
        </button>
      </div>
    </Modal>
  );
}
