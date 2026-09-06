# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Natural-language play: a Claude tool-use loop over the game engine.

The frontend's chat mode posts a message here; Claude interprets the player's
intent, drives the game with the ``game_command`` tool (and can consult the
scene and map), then narrates the result -- keeping the game's own responses
authoritative.  Uses the official Anthropic SDK with a manual tool loop.
"""
from __future__ import annotations

import json
import os

from . import cavemap
from .scene import SceneStore
from .session import Session

MODEL = os.environ.get("ADVENT_LLM_MODEL", "claude-opus-5")
MAX_TURNS = 12  # safety cap on tool-loop iterations per message

SYSTEM = """\
You are the game master for the classic text adventure Colossal Cave Adventure.
The human plays; you interpret their intent and drive the real game engine with
the game_command tool, then narrate what happens in your own words while staying
faithful to the game's responses (you may quote them).

Rules:
- To act in the world, call game_command with a one- or two-word command
  ("north", "take lamp", "xyzzy", "kill dragon"). Only the first five letters of
  each word matter; the parser takes at most two words.
- The game's responses are authoritative -- never invent outcomes. If a command
  fails or the game says something unexpected, relay that.
- The game sometimes asks yes/no questions (reincarnation after death, quitting);
  answer them by calling game_command with "yes" or "no".
- Use get_scene when the player asks what the place looks like, and get_map when
  they ask about the layout of the cave. The UI shows the image and map itself.
- Keep replies fairly short and evocative, like a game master.
"""

TOOLS = [
    {
        "name": "game_command",
        "description": "Send one command line to the Adventure engine and get its "
                       "reply plus the new game state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string",
                            "description": "A one- or two-word command, e.g. 'take lamp'."},
            },
            "required": ["command"],
        },
    },
    {
        "name": "get_scene",
        "description": "Metadata about the current location's illustration (the UI "
                       "displays the actual image).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_map",
        "description": "A Mermaid map of the cave around the current location.",
        "input_schema": {
            "type": "object",
            "properties": {"depth": {"type": "integer",
                                     "description": "Hops from the current room (default 2)."}},
        },
    },
]


def _system_prompt(session: Session) -> str:
    st = session.state()
    return (
        f"{SYSTEM}\nCurrent situation: {st['name']} (room #{st['location']}). "
        f"Score {st['score']}/{st['max_score']}, {st['turns']} turns. "
        f"Carrying: {', '.join(st['inventory']) or 'nothing'}."
    )


def _execute(name: str, args: dict, session: Session, scenes: SceneStore, data) -> dict:
    if name == "game_command":
        r = session.command(args.get("command", ""))
        s = r["state"]
        return {"output": r["output"], "ended": r["ended"], "location": s["location"],
                "name": s["name"], "score": s["score"], "inventory": s["inventory"],
                "visible_objects": s["visible_objects"], "exits": s["exits"]}
    if name == "get_scene":
        sc = scenes.get(data, session.game.loc)
        return {"location": sc["location"], "prompt": sc["prompt"], "cached": sc["cached"]}
    if name == "get_map":
        depth = args.get("depth", 2)
        payload = cavemap.map_payload(data, center=session.game.loc, depth=depth)
        return {"mermaid": payload["mermaid"], "rooms": payload["node_count"]}
    return {"error": f"unknown tool: {name}"}


def run_chat(session: Session, history: list, message: str, *,
             scenes: SceneStore, data, model: str = MODEL) -> tuple[str, list]:
    """Run one chat turn; return (assistant_reply, updated_history)."""
    import anthropic

    client = anthropic.Anthropic()
    messages = list(history) + [{"role": "user", "content": message}]

    response = None
    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=_system_prompt(session),
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results = []
        for block in response.content:
            if block.type == "tool_use":
                out = _execute(block.name, block.input or {}, session, scenes, data)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})

    reply = "".join(b.text for b in response.content if b.type == "text").strip()
    return reply or "(the game master is silent)", messages
