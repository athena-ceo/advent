# Copyright (c) 2026 Athena Decisions Systems SAS.
"""An MCP server exposing the Adventure engine as tools.

Each game is a server-side session driven a command at a time.  A client (an
LLM chat UI, say) calls ``new_game`` to start, then ``game_command`` to play,
reading structured ``state`` and the full ``transcript`` to reason over the
game's history and context.

Run it::

    python -m advent.mcp_server                 # stdio (local MCP clients)
    python -m advent.mcp_server --http --port 8040   # streamable HTTP (hosting)
"""
from __future__ import annotations

import argparse

from mcp.server.mcpserver import MCPServer

from .session import SessionManager

INSTRUCTIONS = """\
This server hosts Colossal Cave Adventure (the original 350-point Crowther &
Woods game). Play by calling tools:

- new_game() starts a game and returns a session_id plus the opening text. The
  game first asks "WOULD YOU LIKE INSTRUCTIONS?" -- answer it with game_command.
- game_command(session_id, command) sends one line (e.g. "no", "enter",
  "take lamp", "xyzzy", "go west", "kill dragon"). It returns the game's reply
  and the resulting structured state. The parser reads only the first five
  letters of each word and understands at most a two-word command.
- Yes/no prompts (reincarnation, quit, hints) come back as ordinary output;
  answer them with the next game_command ("yes"/"no").
- get_state / get_transcript let you inspect the current situation and the whole
  history so far.

Relay the game's own text to the player; use the structured state to keep track
of location, inventory, score and whether the game has ended.
"""

server = MCPServer("adventure", instructions=INSTRUCTIONS)
sessions = SessionManager()


@server.custom_route("/health", methods=["GET"])
async def health(request):
    """Liveness probe (served in HTTP mode) used by the deploy smoke test."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "server": "adventure",
                         "sessions": len(sessions.list())})


def _not_found(session_id: str) -> dict:
    return {"error": f"no such session: {session_id!r}. Call new_game first."}


@server.tool()
def new_game(seed: int | None = None) -> dict:
    """Start a new game. Returns {session_id, intro, state}.

    `intro` is the opening banner ending in "WOULD YOU LIKE INSTRUCTIONS?" --
    answer it with game_command(session_id, "yes"|"no"). Pass `seed` for a
    reproducible game.
    """
    session = sessions.create(seed=seed)
    return {"session_id": session.id, "intro": session.intro, "state": session.state()}


@server.tool()
def game_command(session_id: str, command: str) -> dict:
    """Send one command line to a game. Returns {output, state, ended}.

    `command` is a one- or two-word Adventure command ("take lamp", "n", "xyzzy",
    "kill troll", "yes"). Only the first five letters of each word matter.
    """
    session = sessions.get(session_id)
    if session is None:
        return _not_found(session_id)
    return session.command(command)


@server.tool()
def get_state(session_id: str) -> dict:
    """Return the current structured state of a game (no turn is taken).

    Includes location, description, visible objects, inventory, exits, score,
    turn count and whether the game has ended.
    """
    session = sessions.get(session_id)
    if session is None:
        return _not_found(session_id)
    return session.state()


@server.tool()
def get_transcript(session_id: str) -> dict:
    """Return the full text transcript of a game so far, for history/context."""
    session = sessions.get(session_id)
    if session is None:
        return _not_found(session_id)
    return {"session_id": session_id, "transcript": session.transcript()}


@server.tool()
def save_game(session_id: str) -> dict:
    """Snapshot a game so it can be restored later. Returns {save_id}.

    The game keeps playing; the snapshot is a point-in-time copy. Restore it
    with restore_game(save_id), which starts a fresh session from the snapshot.
    """
    save_id = sessions.save(session_id)
    if save_id is None:
        return _not_found(session_id)
    return {"save_id": save_id}


@server.tool()
def restore_game(save_id: str) -> dict:
    """Start a new game from a saved snapshot. Returns {session_id, output, state}.

    `output` is the re-described current room. Use the returned session_id for
    subsequent game_command calls.
    """
    session = sessions.restore(save_id)
    if session is None:
        return {"error": f"no such save: {save_id!r}"}
    return {"session_id": session.id, "output": session.intro, "state": session.state()}


@server.tool()
def list_games() -> dict:
    """List active game sessions with a brief status for each."""
    return {"sessions": [
        {"session_id": s.id, "location": s.game.loc, "turns": s.game.turns,
         "ended": s.ended}
        for s in sessions.list()
    ]}


@server.tool()
def end_game(session_id: str) -> dict:
    """Discard a game session and free its resources."""
    return {"closed": sessions.close(session_id)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adventure MCP server.")
    parser.add_argument("--http", action="store_true",
                        help="serve over streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8040)
    args = parser.parse_args(argv)

    if args.http:
        server.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
