#!/usr/bin/env python3
# Copyright (c) 2026 Athena Decisions Systems SAS.
"""End-to-end smoke test against a running Adventure backend.

Checks the health probe, then drives a short game through the MCP endpoint to
prove the server actually plays: start a game, decline instructions, walk into
the building, take the lamp, and confirm the state advances.

    SMOKE_BASE_URL=http://localhost:8040 python3 scripts/smoke_test.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost:8040").rstrip("/")


def check_health() -> None:
    with urllib.request.urlopen(f"{BASE}/health", timeout=10) as r:
        body = json.loads(r.read().decode())
    assert body.get("status") == "ok", f"unexpected health body: {body}"
    print(f"[smoke] health ok: {body}")


async def play() -> None:
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(f"{BASE}/mcp") as streams:
        read, write = streams[0], streams[1]
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert {"new_game", "game_command"} <= names, f"missing tools: {names}"
            print(f"[smoke] {len(names)} tools: {sorted(names)}")

            res = await session.call_tool("new_game", {"seed": 1})
            sid = json.loads(res.content[0].text)["session_id"]

            for cmd in ["no", "enter", "take lamp"]:
                res = await session.call_tool(
                    "game_command", {"session_id": sid, "command": cmd})
                data = json.loads(res.content[0].text)
            state = data["state"]
            assert state["location"] == 3, f"expected building (3), got {state['location']}"
            assert "BRASS LANTERN" in state["inventory"], state["inventory"]
            print(f"[smoke] played 3 turns: loc={state['location']} "
                  f"inventory={state['inventory']} score={state['score']}")


def main() -> int:
    check_health()
    asyncio.run(play())
    print("[smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
