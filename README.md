<!-- Copyright (c) 2026 Athena Decisions Systems SAS. -->

# Adventure

A faithful Python port of the original **350-point Colossal Cave Adventure**
(Crowther & Woods), driven directly by the historic `advent.dat` database and
translated label-for-label from the PDP-10 FORTRAN source `advent.for` (both in
the repository root).

This is Phase 0 + 1 of the port: a clean, self-contained engine with a terminal
front end and a fidelity test suite. The web UI, AI-generated location art, and
the MCP tool server come in later phases — the engine is built to support them
(command-at-a-time play, fully serialisable state).

## Layout

| Path | What it is |
|---|---|
| [`advent/data.py`](advent/data.py) | Parser: `advent.dat` → a structured `GameData` |
| [`advent/game.py`](advent/game.py) | The engine — a faithful port of `advent.for` |
| [`advent/rng.py`](advent/rng.py) | Seedable random source (`ran`/`pct`) |
| [`advent/cli.py`](advent/cli.py) | Terminal front end |
| [`advent/session.py`](advent/session.py) | Command-at-a-time sessions over the engine |
| [`advent/mcp_server.py`](advent/mcp_server.py) | MCP server exposing the game as tools |
| [`tests/`](tests/) | Parser, engine, and session/MCP tests |

## Play

```bash
python -m advent            # random game
python -m advent --seed 12  # reproducible game
```

## MCP server

The engine is exposed as an [MCP](https://modelcontextprotocol.io) server so an
LLM chat UI can play the game through tool calls and reason over its state and
history. Each game is a server-side session driven one command at a time; yes/no
prompts (reincarnation, quit, hints) come back as ordinary output to be answered
by the next call.

```bash
pip install -e ".[mcp]"
python -m advent.mcp_server                    # stdio (local MCP clients)
python -m advent.mcp_server --http --port 8040 # streamable HTTP (hosting)
```

Tools: `new_game`, `game_command`, `get_state`, `get_transcript`, `list_games`,
`end_game`. `get_state` returns structured fields — location, description,
visible objects, inventory, exits, score, turns, and the closing/ended flags.

## Design notes

- **The data file is the game.** `advent.dat` holds every room, object, message,
  the travel map, vocabulary, hints and scoring. The parser preserves the
  original encodings (notably the flat `travel` array and its `key` index) so the
  engine can mirror the FORTRAN exactly.
- **Control flow is preserved.** The FORTRAN is one routine wired with `GOTO`s.
  Each numbered label becomes a small method (`_l2000` == FORTRAN label 2000)
  returning the next label; a dispatch loop runs them. Statement numbers appear
  in comments so the two can be read side by side.
- **State is plain, serialisable attributes** — ready for save/restore, a web
  backend, or an MCP server to inspect and drive a command at a time.
- **Lightly modernised**: the FORTRAN's mixed-case interface strings are kept as
  written; the all-caps styling of the classic game is left to the UI layer. The
  "cave hours"/wizard gating (a 1977 timesharing artefact) is dropped.

## Testing & fidelity

```bash
pip install -e ".[test]"    # installs pytest + the reference `adventure` package
python -m pytest -q
```

Brandon Rhodes' independently-written [`adventure`](https://pypi.org/project/adventure/)
package (a faithful port of the *same* `advent.dat`/`advent.for`) is used only as
a **test oracle**, never as a runtime dependency:

- **Parser** — every room description, object message, arbitrary message and
  object placement is cross-checked against the reference (`test_parser.py`).
- **Engine** — a broad deterministic script is diffed **line-for-line** against
  the reference and matches exactly (`test_deterministic_matches_reference`).
  The comparison stays in the pre-Hall-of-Mists region because past that point
  both engines' random dwarf/pirate subsystems fire, and the two use different
  RNG implementations, so their random *timing* legitimately diverges.
- A full 269-command canonical solve runs end to end through the engine,
  exercising the deep mechanics (mazes, troll bridge, dragon, treasures,
  cave-closing endgame, scoring).
