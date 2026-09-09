// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useState } from "react";
import { api, type AdminGame, type AdminUser } from "../api";
import { Modal, field, plainBtn, primaryBtn } from "./Modal";

const when = (t: number) => new Date(t * 1000).toLocaleString();

export function AdminModal({ onClose }: { onClose: () => void }) {
  const [pw, setPw] = useState("");
  const [authed, setAuthed] = useState(false);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [games, setGames] = useState<AdminGame[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async (password: string) => {
    setBusy(true); setErr(null);
    try {
      const [u, g] = await Promise.all([api.adminUsers(password), api.adminGames(password)]);
      setUsers(u.users); setGames(g.games); setAuthed(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally { setBusy(false); }
  };

  const reset = async () => {
    if (!confirm("Wipe ALL games and reset the leaderboard? This cannot be undone.")) return;
    const r = await api.adminReset(pw).catch((e) => { setErr(String(e.message || e)); return null; });
    if (r) await load(pw);
  };
  const del = async (id: string, name: string) => {
    if (!confirm(`Delete user "${name}" and all their games?`)) return;
    await api.adminDeleteUser(pw, id).catch((e) => setErr(String(e.message || e)));
    await load(pw);
  };

  return (
    <Modal title="Admin" onClose={onClose} wide>
      {!authed ? (
        <form onSubmit={(e) => { e.preventDefault(); load(pw); }} className="space-y-3">
          <p className="text-cave-300">Enter the admin password (set as <code>ADVENT_ADMIN_PASSWORD</code> on the server).</p>
          <input className={field} type="password" placeholder="admin password" value={pw} autoFocus
            onChange={(e) => setPw(e.target.value)} />
          {err && <div className="text-red-400 text-xs">{err}</div>}
          <div className="flex justify-end"><button className={primaryBtn} disabled={busy || !pw}>Unlock</button></div>
        </form>
      ) : (
        <>
          {err && <div className="text-red-400 text-xs">{err}</div>}
          <div className="flex items-center justify-between">
            <h3 className="font-serif text-amber-glow/90 text-sm uppercase tracking-wider">Users ({users.length})</h3>
            <button onClick={reset} className={plainBtn}>Reset leaderboard</button>
          </div>
          <div className="max-h-52 overflow-y-auto scroll-thin">
            <table className="w-full text-left">
              <thead><tr className="text-[10px] uppercase tracking-wider text-cave-300">
                <th className="py-1">Name</th><th className="py-1 text-right">Games</th>
                <th className="py-1 text-right">Best</th><th className="py-1">Last seen</th><th></th></tr></thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-t border-cave-700">
                    <td className="py-1">{u.name}{u.is_admin ? <span className="ml-1 text-[10px] text-amber-glow">admin</span> : null}</td>
                    <td className="py-1 text-right text-cave-300">{u.games}</td>
                    <td className="py-1 text-right text-amber-glow">{u.best}</td>
                    <td className="py-1 text-cave-300 text-[11px]">{when(u.last_seen)}</td>
                    <td className="py-1 text-right">
                      <button onClick={() => del(u.id, u.name)} className="text-[11px] text-red-400 hover:underline">delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3 className="font-serif text-amber-glow/90 text-sm uppercase tracking-wider">Recent activity</h3>
          <div className="max-h-52 overflow-y-auto scroll-thin">
            <table className="w-full text-left">
              <thead><tr className="text-[10px] uppercase tracking-wider text-cave-300">
                <th className="py-1">Player</th><th className="py-1 text-right">Score</th>
                <th className="py-1 text-right">Turns</th><th className="py-1 text-right">Room</th>
                <th className="py-1">Updated</th></tr></thead>
              <tbody>
                {games.map((g) => (
                  <tr key={g.id} className="border-t border-cave-700">
                    <td className="py-1">{g.player}{g.ended ? <span className="ml-1 text-[10px] text-amber-glow/80">finished</span> : null}</td>
                    <td className="py-1 text-right text-amber-glow">{g.score}</td>
                    <td className="py-1 text-right text-cave-300">{g.turns}</td>
                    <td className="py-1 text-right text-cave-300">{g.location}</td>
                    <td className="py-1 text-cave-300 text-[11px]">{when(g.updated)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Modal>
  );
}
