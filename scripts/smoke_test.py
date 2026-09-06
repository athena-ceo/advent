#!/usr/bin/env python3
# Copyright (c) 2026 Athena Decisions Systems SAS.
"""End-to-end smoke test against a running Adventure backend.

Checks the health probe, then drives a short game through the REST API to prove
the server actually plays: start a game, decline instructions, walk into the
building, take the lamp, and confirm the state advances (plus the map endpoint).

    SMOKE_BASE_URL=http://localhost:8040 python3 scripts/smoke_test.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost:8040").rstrip("/")


def _get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=15) as r:
        return json.loads(r.read().decode())


def _post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def main() -> int:
    health = _get("/health")
    assert health.get("status") == "ok", f"unexpected health: {health}"
    print(f"[smoke] health ok: {health}")

    sid = _post("/api/games", {"seed": 1})["session_id"]
    for cmd in ["no", "enter", "take lamp"]:
        state = _post(f"/api/games/{sid}/command", {"command": cmd})["state"]
    assert state["location"] == 3, f"expected building (3), got {state['location']}"
    assert "BRASS LANTERN" in state["inventory"], state["inventory"]
    print(f"[smoke] played 3 turns: loc={state['location']} "
          f"inventory={state['inventory']} score={state['score']}")

    m = _get(f"/api/games/{sid}/map?depth=1")
    assert m["center"] == 3 and m["node_count"] >= 2
    print(f"[smoke] map ok: {m['node_count']} rooms around the building")
    print("[smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
