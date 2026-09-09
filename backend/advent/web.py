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

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import cavemap
from .compositor import SceneComposer
from .data import load_default_data
from .scene import STYLES, resolve_style, SceneStore
from .session import SessionManager
from .store import Store
from .text import sentence_case as sc

GAME_DATA = load_default_data()
store = Store()  # ADVENT_DB env; defaults to in-memory (durable in dev/prod compose)
sessions = SessionManager(store=store)
chat_histories: dict[str, list] = {}

_SPRITE_DIR = os.environ.get("ADVENT_SPRITE_CACHE", "./sprite-cache")
_COMPOSITE_DIR = os.environ.get("ADVENT_COMPOSITE_CACHE")  # None -> derived next to scenes
_composers: dict[str, SceneComposer] = {}


def get_composer(style: str | None) -> SceneComposer:
    """A cached SceneComposer for a style (its own scene/sprite/composite dirs)."""
    style = resolve_style(style)
    comp = _composers.get(style)
    if comp is None:
        comp = SceneComposer(SceneStore(style=style), _SPRITE_DIR,
                             composite_dir=_COMPOSITE_DIR)
        _composers[style] = comp
    return comp


# Engine text (output + state) is already sentence-cased at the session boundary
# (see advent.session), so the play endpoints pass it straight through. Only the
# cave map still needs casing here, as its labels come from cavemap, not a session.
def _pretty_state(st: dict) -> dict:
    return st


def _pretty_turn(r: dict) -> dict:
    return r


def _pretty_map(payload: dict) -> dict:
    """Sentence-case the map's node labels (and rebuild the Mermaid from them)."""
    nodes = {n["id"]: sc(n["name"]) for n in payload["graph"]["nodes"]}
    edges = payload["graph"]["edges"]
    payload = dict(payload)
    payload["graph"] = {"nodes": [{"id": i, "name": nm} for i, nm in nodes.items()],
                        "edges": edges}
    payload["mermaid"] = cavemap.to_mermaid(nodes, edges, highlight=payload.get("center"))
    return payload

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


class Credentials(BaseModel):
    name: str
    password: str


class DeleteUser(BaseModel):
    player_id: str


import uuid as _uuid


def _pid(token: str | None, guest: str | None) -> str:
    """Resolve the acting player: a logged-in account (token) wins, else the
    browser's guest id, else a fresh guest. Always a tracked player row."""
    if token:
        user = store.user_for_token(token)
        if user:
            store.touch_player(user["id"])
            return user["id"]
    gid = guest or _uuid.uuid4().hex[:12]
    store.touch_player(gid)
    return gid


def _admin(x_admin: str | None):
    secret = os.environ.get("ADVENT_ADMIN_PASSWORD")
    if not secret:
        raise HTTPException(status_code=503, detail="admin is not configured on this server")
    if x_admin != secret:
        raise HTTPException(status_code=403, detail="bad admin password")


def _session(session_id: str, player_id: str | None = None):
    # Rehydrate from the store if the game isn't in memory (evicted or restarted).
    session = sessions.reattach(session_id, player_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"no such session: {session_id}")
    return session


@app.get("/health")
def health():
    return {"status": "ok", "server": "adventure", "sessions": len(sessions.list())}


@app.post("/api/games")
def new_game(body: NewGame,
             x_advent_token: str | None = Header(None),
             x_advent_player: str | None = Header(None)):
    pid = _pid(x_advent_token, x_advent_player)
    session = sessions.create(seed=body.seed, player_id=pid)
    return {"session_id": session.id, "intro": sc(session.intro),
            "state": _pretty_state(session.state()), "player": store.player(pid)}


@app.post("/api/games/{session_id}/command")
def command(session_id: str, body: Command,
            x_advent_token: str | None = Header(None),
            x_advent_player: str | None = Header(None)):
    session = _session(session_id, _pid(x_advent_token, x_advent_player))
    r = session.command(body.command)
    sessions.persist(session)
    return _pretty_turn(r)


@app.get("/api/games/{session_id}/state")
def state(session_id: str):
    return _pretty_state(_session(session_id).state())


@app.get("/api/games/{session_id}/transcript")
def transcript(session_id: str):
    # Interleaved log (commands + replies) so a reload rebuilds the whole
    # conversation. Game replies are sentence-cased; player commands shown as typed.
    log = [{"kind": e["kind"],
            "text": sc(e["text"]) if e["kind"] == "game" else e["text"]}
           for e in _session(session_id).log()]
    return {"session_id": session_id, "log": log}


@app.post("/api/games/{session_id}/save")
def save_game(session_id: str):
    _session(session_id)
    return {"save_id": sessions.save(session_id)}


@app.post("/api/restore")
def restore_game(body: Restore,
                 x_advent_token: str | None = Header(None),
                 x_advent_player: str | None = Header(None)):
    session = sessions.restore(body.save_id, player_id=_pid(x_advent_token, x_advent_player))
    if session is None:
        raise HTTPException(status_code=404, detail=f"no such save: {body.save_id}")
    return {"session_id": session.id, "output": sc(session.intro),
            "state": _pretty_state(session.state())}


# -- accounts (name + password; guests are claimed on register/login) --------

@app.post("/api/auth/register")
def auth_register(body: Credentials, x_advent_player: str | None = Header(None)):
    from .store import AuthError
    try:
        user, token = store.register(body.name, body.password, guest_id=x_advent_player)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"user": user, "token": token}


@app.post("/api/auth/login")
def auth_login(body: Credentials, x_advent_player: str | None = Header(None)):
    from .store import AuthError
    try:
        user, token = store.login(body.name, body.password, guest_id=x_advent_player)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"user": user, "token": token}


@app.post("/api/auth/logout")
def auth_logout(x_advent_token: str | None = Header(None)):
    store.logout(x_advent_token)
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(x_advent_token: str | None = Header(None),
            x_advent_player: str | None = Header(None)):
    user = store.user_for_token(x_advent_token) if x_advent_token else None
    return {"user": user or (store.player(x_advent_player) if x_advent_player else None)}


@app.get("/api/leaderboard")
def leaderboard(limit: int = 20):
    return {"entries": store.leaderboard(min(max(limit, 1), 100))}


@app.get("/api/metrics")
def metrics():
    return store.metrics()


# -- admin (gated by the ADVENT_ADMIN_PASSWORD env, sent as X-Advent-Admin) ---

@app.get("/api/admin/users")
def admin_users(x_advent_admin: str | None = Header(None)):
    _admin(x_advent_admin)
    return {"users": store.list_users()}


@app.get("/api/admin/games")
def admin_games(x_advent_admin: str | None = Header(None)):
    _admin(x_advent_admin)
    return {"games": store.recent_games()}


@app.post("/api/admin/reset-leaderboard")
def admin_reset(x_advent_admin: str | None = Header(None)):
    _admin(x_advent_admin)
    return {"removed": store.reset_leaderboard()}


@app.post("/api/admin/delete-user")
def admin_delete_user(body: DeleteUser, x_advent_admin: str | None = Header(None)):
    _admin(x_advent_admin)
    store.delete_user(body.player_id)
    return {"ok": True}


@app.get("/api/styles")
def styles():
    return {"styles": list(STYLES), "default": resolve_style(None)}


@app.get("/api/games/{session_id}/scene")
def scene(session_id: str, style: str | None = None):
    session = _session(session_id)
    result = get_composer(style).render(GAME_DATA, session.game.loc,
                                        session.game.visible_objects())
    result["name"] = sc(cavemap.cave_graph(GAME_DATA)[0].get(session.game.loc))
    return result


@app.get("/api/scene/{location}")
def scene_at(location: int, style: str | None = None):
    return get_composer(style).scenes.get(GAME_DATA, location)


@app.get("/api/games/{session_id}/map")
def game_map(session_id: str, depth: int | None = None, direction: str = "LR"):
    session = _session(session_id)
    return _pretty_map(cavemap.map_payload(GAME_DATA, center=session.game.loc,
                                           depth=depth, direction=direction))


@app.get("/api/map")
def full_map(from_location: int | None = None, depth: int | None = None,
             direction: str = "LR"):
    return _pretty_map(cavemap.map_payload(GAME_DATA, center=from_location,
                                           depth=depth, direction=direction))


@app.post("/api/games/{session_id}/chat")
def chat(session_id: str, body: ChatMessage):
    """Natural-language turn: Claude drives the game and narrates the result."""
    session = _session(session_id)
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise HTTPException(status_code=503,
                            detail="chat mode needs ANTHROPIC_API_KEY on the server")
    from .chat import run_chat

    history = chat_histories.get(session_id, [])
    reply, history = run_chat(session, history, body.message,
                              scenes=get_composer(None).scenes, data=GAME_DATA)
    chat_histories[session_id] = history
    sessions.persist(session)
    # The LLM reply is already normal prose; only prettify the engine state.
    return {"reply": reply, "state": _pretty_state(session.state())}


def main() -> int:
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8040"))
    uvicorn.run("advent.web:app", host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
