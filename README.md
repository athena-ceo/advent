<!-- Copyright (c) 2026 Athena Decisions Systems SAS. -->

# Adventure

A faithful Python port of the original **350-point Colossal Cave Adventure**
(Crowther & Woods), plus an MCP server that exposes the game as tools so an LLM
chat UI can play it and reason over its state. Driven directly by the historic
`advent.dat` database and translated label-for-label from the FORTRAN source.

## Repository layout

```
fortran/        Original PDP-10 source (advent.for, advent.dat, advent.mic, advent.readme)
backend/        Python app
  advent/       The engine + MCP server package
  tests/        Parser, engine, and session/MCP tests
  Dockerfile    Backend container (MCP server over HTTP)
  pyproject.toml
frontend/       React UI (imaging + chat) — added in the UI phase
nginx/          Path-based location block for apps.athenadecisions.com
scripts/        smoke_test.py (health + MCP round-trip)
docker-compose.{dev,server}.yml
advent.sh       Control script (start/stop/logs/health/smoke/test/deploy)
.github/workflows/ci.yml
```

The historic FORTRAN in [`fortran/`](fortran/) is the reference the port was
built from; the engine runs entirely on the Python in `backend/`.

## Quick start (local)

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e "./backend[test]"     # engine + MCP server + test/oracle deps

python -m advent                     # play in the terminal
python -m advent.mcp_server          # run the MCP server (stdio)
python -m pytest backend/tests -q    # run the tests
```

## Play through an LLM (MCP)

The engine is exposed as an [MCP](https://modelcontextprotocol.io) server. Each
game is a server-side session driven one command at a time; yes/no prompts
(reincarnation, quit, hints) come back as ordinary output answered by the next
call. Tools: `new_game`, `game_command`, `get_state`, `get_transcript`,
`save_game`, `restore_game`, `get_map`, `get_scene`, `list_games`, `end_game`.
`get_state` returns fields — location, description, visible objects, inventory,
exits, score, turns, closing/ended. `get_map` returns a Mermaid graph of the
cave derived from the travel table (full or a subgraph around a room);
`get_scene` returns the current location's illustration (generated on first
request and cached — a placeholder card today, an open-weights image model
later) plus the exact per-room image prompt.

**Claude Code (this repo):** copy [`.mcp.json.example`](.mcp.json.example) to
`.mcp.json`, set the `command` to your venv's Python, and start a new Claude Code
session — it will prompt to approve the `adventure` server, after which you can
say "start a game of Adventure and play it with me".

**Claude Desktop (macOS):** edit
`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "adventure": {
      "command": "/ABSOLUTE/PATH/TO/advent/.venv/bin/python",
      "args": ["-m", "advent.mcp_server"]
    }
  }
}
```

(Windows: `%APPDATA%\Claude\claude_desktop_config.json`.) Restart Claude Desktop.

## Docker & deploy (apps.athenadecisions.com)

Served path-based at `/advent` (backend container 8040 — distinct from
golden-path 8020 and xcape 8030; the React frontend will take 3040).

```bash
./advent.sh start dev      # build + run the backend locally
./advent.sh health dev     # curl the health probe
./advent.sh smoke dev      # health + MCP round-trip against the running server
./advent.sh deploy prod    # git pull, build, up, health check (on the server)
```

One-time on the server: paste the blocks from
[`nginx/advent-apps-location.conf`](nginx/advent-apps-location.conf) into the
`apps.athenadecisions.com` server block, then `sudo nginx -t && sudo systemctl
reload nginx`. The MCP endpoint is then at
`https://apps.athenadecisions.com/advent/mcp`.

## CI

Every push/PR runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml):
backend pytest, plus a Docker smoke test that builds the image, boots the
container, and drives a short game through the MCP endpoint.

## Design notes

- **The data file is the game.** `advent.dat` holds every room, object, message,
  the travel map, vocabulary, hints and scoring; the parser preserves the
  original encodings so the engine mirrors the FORTRAN.
- **Control flow is preserved.** Each FORTRAN `GOTO` label is a small method
  (`_l2000` == label 2000) run by a dispatch loop.
- **State is plain, serialisable attributes**, played a command at a time —
  ready for save/restore, the web backend, and the MCP tools.
- Brandon Rhodes' [`adventure`](https://pypi.org/project/adventure/) package is
  used only as a **test oracle** (parser cross-check + line-for-line engine diff
  on deterministic play), never at runtime.
