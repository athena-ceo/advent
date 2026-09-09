# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Command-at-a-time sessions over the (blocking) Adventure engine.

The engine is a faithful port of a routine that blocks on input mid-turn (for
yes/no prompts: reincarnation, quit confirmation, hints, the dragon).  Rather
than rewrite that control flow, each session runs the engine on its own thread
and exchanges lines through queues: :meth:`Session.command` sends one line and
collects everything the engine prints until it next asks for input (or the game
ends).  A yes/no prompt therefore simply comes back as the output of one call,
to be answered by the next -- which is exactly how a chat UI or MCP client wants
to drive it.
"""
from __future__ import annotations

import queue
import threading
import time
import uuid

from .game import Game

# Sentinels placed on the output queue by the engine thread.
_NEED_INPUT = object()  # engine is now blocked waiting for the next line
_DONE = object()        # engine thread has finished (game over / EOF)


class Session:
    def __init__(self, seed: int | None = None, session_id: str | None = None,
                 resume_state: dict | None = None):
        self.id = session_id or uuid.uuid4().hex[:12]
        self.seed = seed
        self.created_at = time.time()
        self.last_active = self.created_at
        self.ended = False
        self._resume_state = resume_state
        self.game = Game(seed=seed)
        if resume_state is not None:
            self.game.load_state(resume_state)
        self._in: queue.Queue = queue.Queue()
        self._out: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name=f"advent-{self.id}",
                                        daemon=True)
        self._thread.start()
        # For a fresh game this is the welcome banner + "instructions?" prompt;
        # for a restored game it is the re-described current room.
        self.intro = self._pump(None)
        # An interleaved play log (commands + their output) so a reload can
        # rebuild the whole conversation, not just the game's replies.
        self._log: list[dict] = []
        if self.intro:
            self._log.append({"kind": "game", "text": self.intro})

    # -- engine thread ------------------------------------------------------

    def _read_line(self) -> str:
        self._out.put(_NEED_INPUT)
        line = self._in.get()
        if line is None:
            raise EOFError
        return line

    def _run(self) -> None:
        try:
            if self._resume_state is not None:
                self.game.resume(self._read_line, self._out.put)
            else:
                self.game.run(self._read_line, self._out.put)
        finally:
            self._out.put(_DONE)

    def _pump(self, line: str | None) -> str:
        if line is not None:
            self._in.put(line)
        chunks: list[str] = []
        while True:
            item = self._out.get()
            if item is _NEED_INPUT:
                break
            if item is _DONE:
                self.ended = True
                break
            chunks.append(item)
        return "\n\n".join(chunks)

    # -- public API ---------------------------------------------------------

    def command(self, text: str) -> dict:
        """Send one command line; return its output and the resulting state."""
        with self._lock:
            self.last_active = time.time()
            if self.ended:
                return {"output": "", "ended": True, "state": self.state()}
            output = self._pump(text)
            self._log.append({"kind": "you", "text": text})
            if output:
                self._log.append({"kind": "game", "text": output})
            return {"output": output, "ended": self.ended, "state": self.state()}

    def state(self) -> dict:
        st = self.game.state()
        st["ended"] = self.ended
        st["session_id"] = self.id
        if self.ended:
            score, mxscor = self.game.compute_score()
            st["score"], st["max_score"] = score, mxscor
        return st

    def transcript(self) -> list[str]:
        return list(self.game.transcript)

    def log(self) -> list[dict]:
        """Interleaved play log: [{kind: 'you'|'game', text}], for UI resume."""
        return list(self._log)

    def close(self) -> None:
        """Unblock and retire the session's engine thread."""
        if not self.ended:
            self._in.put(None)
            self.ended = True


class SessionManager:
    """In-memory registry of sessions with simple FIFO eviction."""

    def __init__(self, max_sessions: int = 200):
        self.max_sessions = max_sessions
        self._sessions: dict[str, Session] = {}
        self._saves: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _register(self, session: Session) -> None:
        self._sessions[session.id] = session
        if len(self._sessions) > self.max_sessions:
            oldest = min(self._sessions.values(), key=lambda s: s.last_active)
            self._sessions.pop(oldest.id, None)
            oldest.close()

    def create(self, seed: int | None = None) -> Session:
        session = Session(seed=seed)
        with self._lock:
            self._register(session)
        return session

    def save(self, session_id: str) -> str | None:
        """Snapshot a session's game; return a save id, or None if not found."""
        session = self.get(session_id)
        if session is None:
            return None
        save_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._saves[save_id] = session.game.save_state()
        return save_id

    def restore(self, save_id: str) -> Session | None:
        """Start a new session from a saved snapshot; None if the id is unknown."""
        with self._lock:
            blob = self._saves.get(save_id)
        if blob is None:
            return None
        session = Session(resume_state=blob)
        with self._lock:
            self._register(session)
        return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            return self._sessions.get(session_id)

    def close(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            return True
        return False

    def list(self) -> list[Session]:
        with self._lock:
            return list(self._sessions.values())
