# Copyright (c) 2026 Athena Decisions Systems SAS.
"""HTTP backend for the Adventure web app.

A small REST API the React front end uses to play directly (start a game, send
commands, read state, fetch the location image and the cave map, save/restore),
plus a Claude-driven ``/api/chat`` endpoint for the natural-language mode (see
``chat.py``).  The MCP server (``advent.mcp_server``) is the parallel surface
for external LLM clients; both drive the same engine code.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import cavemap
from .data import load_default_data
from .scene import SceneStore
from .session import SessionManager

GAME_DATA = load_default_data()
sessions = SessionManager()
scenes = SceneStore()
chat_histories: dict[str, list] = {}

app = FastAPI(title="Adventure", version="0.1.0")

_origins = os.environ.get("ADVENT_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewGame(BaseModel):
    seed: int | None = None


class Command(BaseModel):
    command: str


class Restore(BaseModel):
    save_id: str


class ChatMessage(BaseModel):
    message: str


def _session(session_id: str):
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"no such session: {session_id}")
    return session


@app.get("/health")
def health():
    return {"status": "ok", "server": "adventure", "sessions": len(sessions.list())}


@app.post("/api/games")
def new_game(body: NewGame):
    session = sessions.create(seed=body.seed)
    return {"session_id": session.id, "intro": session.intro, "state": session.state()}


@app.post("/api/games/{session_id}/command")
def command(session_id: str, body: Command):
    return _session(session_id).command(body.command)


@app.get("/api/games/{session_id}/state")
def state(session_id: str):
    return _session(session_id).state()


@app.get("/api/games/{session_id}/transcript")
def transcript(session_id: str):
    return {"session_id": session_id, "transcript": _session(session_id).transcript()}


@app.post("/api/games/{session_id}/save")
def save_game(session_id: str):
    _session(session_id)
    return {"save_id": sessions.save(session_id)}


@app.post("/api/restore")
def restore_game(body: Restore):
    session = sessions.restore(body.save_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"no such save: {body.save_id}")
    return {"session_id": session.id, "output": session.intro, "state": session.state()}


@app.get("/api/games/{session_id}/scene")
def scene(session_id: str):
    session = _session(session_id)
    result = scenes.get(GAME_DATA, session.game.loc)
    result["name"] = cavemap.cave_graph(GAME_DATA)[0].get(session.game.loc)
    return result


@app.get("/api/scene/{location}")
def scene_at(location: int):
    return scenes.get(GAME_DATA, location)


@app.get("/api/games/{session_id}/map")
def game_map(session_id: str, depth: int | None = None, direction: str = "LR"):
    session = _session(session_id)
    return cavemap.map_payload(GAME_DATA, center=session.game.loc, depth=depth,
                               direction=direction)


@app.get("/api/map")
def full_map(from_location: int | None = None, depth: int | None = None,
             direction: str = "LR"):
    return cavemap.map_payload(GAME_DATA, center=from_location, depth=depth,
                               direction=direction)


@app.post("/api/games/{session_id}/chat")
def chat(session_id: str, body: ChatMessage):
    """Natural-language turn: Claude drives the game and narrates the result."""
    session = _session(session_id)
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise HTTPException(status_code=503,
                            detail="chat mode needs ANTHROPIC_API_KEY on the server")
    from .chat import run_chat

    history = chat_histories.get(session_id, [])
    reply, history = run_chat(session, history, body.message, scenes=scenes, data=GAME_DATA)
    chat_histories[session_id] = history
    return {"reply": reply, "state": session.state()}


def main() -> int:
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8040"))
    uvicorn.run("advent.web:app", host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
