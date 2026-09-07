// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect, useRef, useState } from "react";

export function CommandBar({ onSend, disabled, placeholder }: {
  onSend: (cmd: string) => void; disabled?: boolean; placeholder?: string;
}) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Keep the keyboard in the command box: focus on mount and whenever a command
  // finishes (disabled: true -> false), which also recovers focus after a pill
  // click elsewhere in the UI.
  useEffect(() => { if (!disabled) inputRef.current?.focus(); }, [disabled]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = value.trim();
    if (!v || disabled) return;
    onSend(v);
    setValue("");
    inputRef.current?.focus();
  };

  return (
    <form onSubmit={submit} className="flex gap-2 border-t border-cave-600 p-3 bg-cave-800">
      <span className="font-mono text-amber-glow self-center">&gt;</span>
      <input
        ref={inputRef}
        autoFocus
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder ?? "enter a command…"}
        className="flex-1 bg-cave-900 border border-cave-600 rounded px-3 py-2 font-mono text-sm outline-none focus:border-amber-glow/60"
      />
      <button disabled={disabled}
        className="px-4 rounded bg-cave-700 border border-cave-600 hover:border-amber-glow/60 text-sm disabled:opacity-50">
        send
      </button>
    </form>
  );
}
