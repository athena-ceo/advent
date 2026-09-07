# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Tests for the command-at-a-time session layer and the MCP tools."""
from __future__ import annotations

import pytest

from advent.session import Session, SessionManager


def test_session_command_flow():
    s = Session(seed=1)
    assert "WOULD YOU LIKE INSTRUCTIONS" in s.intro.upper()

    r = s.command("no")
    assert "STANDING AT THE END OF A ROAD" in r["output"].upper()
    assert r["state"]["location"] == 1 and not r["ended"]

    r = s.command("enter")
    assert r["state"]["location"] == 3
    assert r["state"]["name"]

    r = s.command("take lamp")
    assert "BRASS LANTERN" in [o["name"] for o in r["state"]["inventory"]]

    # A yes/no prompt comes back as ordinary output, answered by the next call.
    r = s.command("quit")
    assert "QUIT" in r["output"].upper() and not r["ended"]
    r = s.command("yes")
    assert r["ended"] and "SCORED" in r["output"].upper()

    # Commands after the game ends are inert.
    r = s.command("look")
    assert r["ended"] and r["output"] == ""
    s.close()


def test_session_manager_lifecycle():
    mgr = SessionManager()
    s = mgr.create(seed=2)
    assert mgr.get(s.id) is s
    assert any(x.id == s.id for x in mgr.list())
    assert mgr.close(s.id) is True
    assert mgr.get(s.id) is None
    assert mgr.close(s.id) is False


def test_manager_evicts_oldest_over_capacity():
    mgr = SessionManager(max_sessions=2)
    a = mgr.create(seed=1)
    b = mgr.create(seed=1)
    c = mgr.create(seed=1)  # should evict a
    assert mgr.get(a.id) is None
    assert mgr.get(b.id) is b and mgr.get(c.id) is c


def test_save_and_restore_round_trip():
    import json

    mgr = SessionManager()
    s = mgr.create(seed=1)
    for c in ["no", "enter", "take lamp", "take keys", "xyzzy", "on", "w"]:
        s.command(c)
    before = s.command("look")["state"]

    save_id = mgr.save(s.id)
    assert save_id
    # The snapshot must be JSON-serialisable (for portability / persistence).
    json.dumps(mgr._saves[save_id])

    # Diverge the original game after saving.
    s.command("e")
    s.command("e")
    assert s.game.loc != before["location"]

    # Restore into a fresh session at the saved point.
    r = mgr.restore(save_id)
    assert r is not None
    st = r.state()
    assert st["location"] == before["location"]
    assert st["inventory"] == before["inventory"]
    assert st["score"] == before["score"]
    # And it keeps playing.
    out = r.command("w")
    assert out["state"]["location"] != before["location"]

    assert mgr.restore("nonexistent") is None
    s.close()
    r.close()


def test_mcp_tools():
    pytest.importorskip("mcp")
    from advent import mcp_server as srv

    r = srv.new_game(seed=1)
    sid = r["session_id"]
    assert r["intro"] and r["state"]["location"] == 0

    out = srv.game_command(sid, "no")
    assert out["state"]["location"] == 1

    st = srv.get_state(sid)
    assert st["max_score"] == 350 and "inventory" in st

    tr = srv.get_transcript(sid)
    assert isinstance(tr["transcript"], list) and tr["transcript"]

    assert "error" in srv.game_command("bogus-id", "look")
    assert any(g["session_id"] == sid for g in srv.list_games()["sessions"])

    # save_game / restore_game tools
    saved = srv.save_game(sid)
    assert "save_id" in saved
    restored = srv.restore_game(saved["save_id"])
    assert restored["state"]["location"] == 1 and restored["session_id"] != sid
    assert "error" in srv.restore_game("nope")

    assert srv.end_game(sid)["closed"] is True
