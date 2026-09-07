<!-- Copyright (c) 2026 Athena Decisions Systems SAS. -->

# Adventure — handoff / machine-switch guide

Everything you need to pick this up on another machine. Backlog is in
[`TODO.md`](TODO.md); architecture details are in [`README.md`](README.md).
We work directly on **`main`** (solo, no branches/PRs).

## What this is
A faithful Python port of the original 350-point Colossal Cave Adventure, plus:
- an **MCP server** exposing the game as tools,
- a **web backend** (FastAPI) with REST direct-play and a Claude-driven chat mode,
- a **React UI** (Classic + Guided modes) with scene images and a live cave map,
- **local open-weights image generation** for per-location art (cached).

## Layout
```
fortran/   original PDP-10 source (reference only)
backend/   Python package `advent` (engine, MCP, web, chat, imagegen, pregen) + tests + Dockerfile
frontend/  React + Vite + TS + Tailwind SPA
nginx/     path-based /advent block for apps.athenadecisions.com
scripts/   smoke_test.py
advent.sh  control script; docker-compose.{dev,server}.yml; .github/workflows/ci.yml
```

## First-time setup on a new machine
1. Clone, then create the backend venv and install (editable):
   ```bash
   python3.12 -m venv .venv && . .venv/bin/activate
   pip install -e "./backend[test]"
   python -m pytest backend/tests -q      # 28 tests should pass
   ```
2. **Secrets**: `cp .env.example .env` and put your real `ANTHROPIC_API_KEY` in
   it (Guided mode only; Classic needs no key). `.env` is git-ignored — it does
   NOT travel with the repo, so recreate it on each machine.
3. **Run it**:
   - Docker (full stack): `./advent.sh start dev` → http://localhost:3040
     (`./advent.sh urls dev` prints the URLs; API docs at :8040/docs).
   - Or locally: `python -m advent.web` (REST :8040) + `cd frontend && npm install && npm run dev` (:3040).
   - Terminal only: `python -m advent`.
   - MCP (Claude Desktop/Code): see README; copy `.mcp.json.example` → `.mcp.json`.

## Image generation (NOT in git — regenerate per machine)
- `scene-cache/` (the generated PNGs) and the `.venv-img` model venv are
  git-ignored. On a new machine there are no images until you generate them; the
  app just shows the placeholder card until then.
- Install the (heavy) image deps into a separate host venv and generate:
  ```bash
  python3.12 -m venv .venv-img && . .venv-img/bin/activate
  pip install -e "./backend[imagegen]"
  python -m advent.pregen --out ./scene-cache            # SDXL-Turbo, offline once weights are cached
  ```
- Model weights cache in `~/.cache/huggingface` (SDXL-Turbo ~7GB first time).
- Docker serves `scene-cache/` via a mounted volume, so generating on the host
  populates the running app immediately (real PNGs preferred over placeholders).
- Style lives in `backend/advent/scene.py` (`STYLE_SURFACE` / `STYLE_UNDERGROUND`
  / `STYLE_TITLE`); the style must stay *modifiers only* — naming architecture
  makes the model ignore the actual room. See TODO for FLUX/PixArt.

## Current state (2026-09-07)
- Engine, MCP, web, React UI, Docker, CI: **working**; 28 tests pass.
- Guided mode works with a real key; prompt rewritten to stay faithful.
- Reload no longer loses progress (session id in `localStorage`, reattaches).
- Room 0 has a real dusk-vista title image; other rooms still have the OLD-style
  cached art pending a full `--overwrite` re-render (see TODO).
- **Not yet deployed** to Athena (compose/nginx/advent.sh ready).

## Gotchas
- Never commit `.venv*/`, `.env`/`.env~`, or `scene-cache/` (all git-ignored;
  history was already purged of an accidental venv + a placeholder `.env~`).
- `pyenv` here has no bare `python`; use the venv's Python or `python3.12`.
- Backend container mounts `./backend` with `--reload`, so backend edits are live
  without rebuilding; frontend changes need `npm run build` (or a container
  rebuild, which needs network for npm).
