# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Durable, tracked play with a real (lightweight) user model.

SQLite, stdlib only. Three concerns:

* **Users** -- a player row is either an anonymous *guest* (name/password NULL)
  or a registered account (unique ``name`` + PBKDF2 ``password_hash``). Auth is
  deliberately low-ceremony: name + password, a random bearer token per login.
* **Games** -- every turn snapshots the engine state (``game.save_state()``) so a
  game survives restarts and cache eviction, keyed to its player.
* **Reporting/admin** -- leaderboard, metrics, and the queries behind a small
  admin view (list users, recent activity, reset the board, delete a user).

Guests play immediately; on register/login their guest games are *claimed* into
the account. Point ``ADVENT_DB`` at a persistent volume (defaults to in-memory).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
import uuid

_SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id            TEXT PRIMARY KEY,
    name          TEXT UNIQUE,        -- NULL for a guest; the login handle + display name
    password_hash TEXT,               -- NULL for a guest
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created       REAL NOT NULL,
    last_seen     REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS games (
    id         TEXT PRIMARY KEY,
    player_id  TEXT NOT NULL,
    seed       INTEGER,
    state      TEXT NOT NULL,
    score      INTEGER NOT NULL DEFAULT 0,
    max_score  INTEGER NOT NULL DEFAULT 0,
    turns      INTEGER NOT NULL DEFAULT 0,
    location   INTEGER NOT NULL DEFAULT 0,
    ended      INTEGER NOT NULL DEFAULT 0,
    started    REAL NOT NULL,
    updated    REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
    token     TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    created   REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS games_player ON games(player_id);
CREATE INDEX IF NOT EXISTS games_score  ON games(score DESC);
CREATE INDEX IF NOT EXISTS games_updated ON games(updated DESC);
"""


# -- password hashing (PBKDF2, stdlib) --------------------------------------

def hash_password(password: str, iterations: int = 100_000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        _algo, iters, salt_b64, hash_b64 = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 base64.b64decode(salt_b64), int(iters))
        return hmac.compare_digest(dk, base64.b64decode(hash_b64))
    except Exception:
        return False


class AuthError(Exception):
    """Raised for register/login problems (name taken, bad credentials)."""


class Store:
    def __init__(self, path: str | None = None):
        self.path = str(path or os.environ.get("ADVENT_DB", ":memory:"))
        if self.path not in (":memory:", ""):
            from pathlib import Path
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript(_SCHEMA)
            self._db.commit()

    # -- players / auth -----------------------------------------------------

    def touch_player(self, player_id: str) -> None:
        """Ensure a (guest) player row exists and bump last_seen."""
        now = time.time()
        with self._lock:
            self._db.execute(
                "INSERT INTO players(id, created, last_seen) VALUES(?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen",
                (player_id, now, now))
            self._db.commit()

    def _public(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        return {"id": row["id"], "name": row["name"], "is_admin": bool(row["is_admin"]),
                "registered": row["name"] is not None}

    def player(self, player_id: str) -> dict | None:
        row = self._db.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
        return self._public(row)

    def _claim(self, guest_id: str | None, user_id: str) -> None:
        """Move a guest's games onto the account (called under lock)."""
        if guest_id and guest_id != user_id:
            self._db.execute("UPDATE games SET player_id=? WHERE player_id=?",
                             (user_id, guest_id))

    def _issue_token(self, player_id: str) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        self._db.execute("INSERT INTO tokens(token, player_id, created) VALUES(?,?,?)",
                         (token, player_id, time.time()))
        return token

    def register(self, name: str, password: str, guest_id: str | None = None) -> tuple[dict, str]:
        """Create an account (claiming the guest's games); returns (user, token)."""
        name = (name or "").strip()
        if not (2 <= len(name) <= 40):
            raise AuthError("name must be 2-40 characters")
        if len(password or "") < 4:
            raise AuthError("password must be at least 4 characters")
        now = time.time()
        with self._lock:
            taken = self._db.execute("SELECT 1 FROM players WHERE name=? COLLATE NOCASE",
                                     (name,)).fetchone()
            if taken:
                raise AuthError("that name is already taken")
            # Upgrade the guest row in place if we have one, else create fresh.
            uid = guest_id or uuid.uuid4().hex[:12]
            first = self._db.execute("SELECT COUNT(*) c FROM players WHERE name IS NOT NULL"
                                     ).fetchone()["c"] == 0
            self._db.execute(
                "INSERT INTO players(id, name, password_hash, is_admin, created, last_seen) "
                "VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
                "password_hash=excluded.password_hash, is_admin=excluded.is_admin, "
                "last_seen=excluded.last_seen",
                (uid, name, hash_password(password), 1 if first else 0, now, now))
            self._claim(guest_id, uid)
            token = self._issue_token(uid)
            self._db.commit()
            return self._public(self._db.execute("SELECT * FROM players WHERE id=?", (uid,)).fetchone()), token

    def login(self, name: str, password: str, guest_id: str | None = None) -> tuple[dict, str]:
        with self._lock:
            row = self._db.execute("SELECT * FROM players WHERE name=? COLLATE NOCASE",
                                   (name.strip(),)).fetchone()
            if row is None or not verify_password(password, row["password_hash"]):
                raise AuthError("wrong name or password")
            self._claim(guest_id, row["id"])
            self._db.execute("UPDATE players SET last_seen=? WHERE id=?", (time.time(), row["id"]))
            token = self._issue_token(row["id"])
            self._db.commit()
            return self._public(row), token

    def user_for_token(self, token: str | None) -> dict | None:
        if not token:
            return None
        row = self._db.execute(
            "SELECT p.* FROM tokens t JOIN players p ON p.id=t.player_id WHERE t.token=?",
            (token,)).fetchone()
        return self._public(row)

    def logout(self, token: str | None) -> None:
        if token:
            with self._lock:
                self._db.execute("DELETE FROM tokens WHERE token=?", (token,))
                self._db.commit()

    # -- games --------------------------------------------------------------

    def save_game(self, game_id: str, player_id: str, seed, state: dict, *,
                  score: int, max_score: int, turns: int, location: int, ended: bool) -> None:
        now = time.time()
        with self._lock:
            self._db.execute(
                "INSERT INTO games(id, player_id, seed, state, score, max_score, turns, "
                "location, ended, started, updated) VALUES(?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, score=excluded.score, "
                "max_score=excluded.max_score, turns=excluded.turns, location=excluded.location, "
                "ended=excluded.ended, updated=excluded.updated, player_id=excluded.player_id",
                (game_id, player_id, seed, json.dumps(state), score, max_score, turns,
                 location, int(ended), now, now))
            self._db.commit()

    def load_state(self, game_id: str) -> dict | None:
        row = self._db.execute("SELECT state FROM games WHERE id=?", (game_id,)).fetchone()
        return json.loads(row["state"]) if row else None

    def game_player(self, game_id: str) -> str | None:
        row = self._db.execute("SELECT player_id FROM games WHERE id=?", (game_id,)).fetchone()
        return row["player_id"] if row else None

    # -- reporting ----------------------------------------------------------

    def leaderboard(self, limit: int = 20) -> list[dict]:
        cur = self._db.execute(
            "SELECT COALESCE(p.name,'guest') AS name, p.name IS NOT NULL AS registered, "
            "  MAX(g.score) AS score, g.max_score, g.turns, g.ended, g.updated "
            "FROM games g LEFT JOIN players p ON p.id=g.player_id "
            "WHERE g.score > 0 "
            "GROUP BY g.player_id ORDER BY score DESC, g.updated DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    def metrics(self, active_window: float = 900.0) -> dict:
        now = time.time(); db = self._db
        def one(q, *a): return db.execute(q, a).fetchone()[0]
        return {
            "players_total": one("SELECT COUNT(*) FROM players"),
            "registered_total": one("SELECT COUNT(*) FROM players WHERE name IS NOT NULL"),
            "games_total": one("SELECT COUNT(*) FROM games"),
            "players_active": one("SELECT COUNT(*) FROM players WHERE last_seen>?", now - active_window),
            "games_active": one("SELECT COUNT(*) FROM games WHERE ended=0 AND updated>?", now - active_window),
            "completions": one("SELECT COUNT(*) FROM games WHERE ended=1"),
            "top_score": one("SELECT COALESCE(MAX(score),0) FROM games"),
            "active_window_min": int(active_window // 60),
        }

    # -- admin --------------------------------------------------------------

    def list_users(self, limit: int = 200) -> list[dict]:
        cur = self._db.execute(
            "SELECT p.id, COALESCE(p.name,'(guest)') AS name, p.is_admin, p.created, p.last_seen, "
            "  COUNT(g.id) AS games, COALESCE(MAX(g.score),0) AS best "
            "FROM players p LEFT JOIN games g ON g.player_id=p.id "
            "GROUP BY p.id ORDER BY p.last_seen DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    def recent_games(self, limit: int = 50) -> list[dict]:
        cur = self._db.execute(
            "SELECT g.id, COALESCE(p.name,'guest') AS player, g.score, g.turns, g.location, "
            "  g.ended, g.updated FROM games g LEFT JOIN players p ON p.id=g.player_id "
            "ORDER BY g.updated DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    def reset_leaderboard(self) -> int:
        """Wipe all game records (the leaderboard). Returns rows removed."""
        with self._lock:
            n = self._db.execute("SELECT COUNT(*) FROM games").fetchone()[0]
            self._db.execute("DELETE FROM games")
            self._db.commit()
            return n

    def delete_user(self, player_id: str) -> None:
        with self._lock:
            self._db.execute("DELETE FROM games WHERE player_id=?", (player_id,))
            self._db.execute("DELETE FROM tokens WHERE player_id=?", (player_id,))
            self._db.execute("DELETE FROM players WHERE id=?", (player_id,))
            self._db.commit()
