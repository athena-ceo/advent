// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useState } from "react";
import { api, setAuthToken, type User } from "../api";
import { Modal, field, primaryBtn } from "./Modal";

export function AuthModal({ onClose, onAuth }: { onClose: () => void; onAuth: (u: User) => void }) {
  const [mode, setMode] = useState<"register" | "login">("register");
  const [name, setName] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const r = mode === "register" ? await api.register(name, pw) : await api.login(name, pw);
      setAuthToken(r.token);
      onAuth(r.user);
      onClose();
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : String(e2));
    } finally { setBusy(false); }
  };

  return (
    <Modal title={mode === "register" ? "Create an account" : "Sign in"} onClose={onClose}>
      <p className="text-cave-300">
        Pick a name and password to save your games and appear on the leaderboard.
        Your current guest progress comes with you.
      </p>
      <form onSubmit={submit} className="space-y-3">
        <input className={field} placeholder="name" value={name} autoFocus
          onChange={(e) => setName(e.target.value)} />
        <input className={field} placeholder="password" type="password" value={pw}
          onChange={(e) => setPw(e.target.value)} />
        {err && <div className="text-red-400 text-xs">{err}</div>}
        <div className="flex items-center justify-between">
          <button type="button" className="text-xs text-cave-300 hover:text-amber-glow underline"
            onClick={() => { setMode(mode === "register" ? "login" : "register"); setErr(null); }}>
            {mode === "register" ? "I already have an account" : "Create an account instead"}
          </button>
          <button className={primaryBtn} disabled={busy || !name || !pw}>
            {mode === "register" ? "Create account" : "Sign in"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
