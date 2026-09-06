// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useState } from "react";

export function CommandBar({ onSend, disabled, placeholder }: {
  onSend: (cmd: string) => void; disabled?: boolean; placeholder?: string;
}) {
  const [value, setValue] = useState("");
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = value.trim();
    if (!v) return;
    onSend(v);
    setValue("");
  };
  return (
    <form onSubmit={submit} className="flex gap-2 border-t border-cave-600 p-3 bg-cave-800">
      <span className="font-mono text-amber-glow self-center">&gt;</span>
      <input
        autoFocus
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder={placeholder ?? "enter a command…"}
        className="flex-1 bg-cave-900 border border-cave-600 rounded px-3 py-2 font-mono text-sm outline-none focus:border-amber-glow/60 disabled:opacity-50"
      />
      <button disabled={disabled}
        className="px-4 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 text-sm disabled:opacity-50">
        send
      </button>
    </form>
  );
}
