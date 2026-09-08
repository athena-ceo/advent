<!-- Copyright (c) 2026 Athena Decisions Systems SAS. -->

# Adventure — backlog

Working notes / backlog. We work directly on `main` (solo project, no PRs).

## Now / next
- [ ] **Re-render the whole cave** with the corrected styles (only room 0 is done;
      the rest of `scene-cache/` is still the old "hijacked" look). Offline, no
      network, SDXL already local:
      `source .venv-img/bin/activate && python -m advent.pregen --out ./scene-cache --overwrite`
- [ ] **Try FLUX.1-schnell** (Apache-2.0, best content+style adherence) once on
      wifi: accept its license on HuggingFace, `hf auth login`, then
      `python -m advent.pregen --out ./scene-cache --overwrite --model black-forest-labs/FLUX.1-schnell`.
      Fallback middle-ground: `PixArt-alpha/PixArt-Sigma-XL-2-1024-MS` (no login).
- [ ] **Deploy to Athena** (`apps.athenadecisions.com/advent`): paste
      `nginx/advent-apps-location.conf` into the shared server block, set a prod
      `.env` (ANTHROPIC_API_KEY), `./advent.sh deploy prod`. Ship the local
      `scene-cache/` up (it's not in git) or regenerate on a GPU box.
- [ ] **GitHub housekeeping**: set the repo default branch to `main`, then delete
      the leftover `master` branch (kept for now because it may be the default).

## Objects & creatures in scenes (next feature)
Layer inventory items and creatures onto room images **without** regenerating
every combination.
- [ ] **Sprite compositing (recommended):** generate one transparent sprite per
      object/creature once (SD has no alpha → cut out with `rembg` or a matte);
      the backend pastes the currently-present sprites onto the base room plate
      based on the engine's `visible_objects`/creatures. Cache each composite by
      `(location, frozenset(present sprite+prop))` — only *visited* states, and
      each is a cheap PIL paste, so cost is linear (rooms + objects), not
      combinatorial. Needs a small per-object `{anchor, scale}` placement config.
- [ ] Optional hero-moment upgrade: AI **inpaint** a few key creatures (dragon,
      troll) into the plate for integrated lighting, cached by the same key.
- [ ] Fallback: draw item/creature markers in the frontend over the image.

## Polish / nice-to-have
- [ ] Guided (LLM) mode: sanity-check behaviour with a real key; tune the system
      prompt in `backend/advent/chat.py` if it still over-narrates.
- [ ] Inline cave map sometimes sits low with dead space; tighten vertical
      centering in `frontend/src/components/MapPanel.tsx`. Stretch: true
      hyperbolic/fisheye focus (needs a custom D3 layout, not Mermaid).
- [ ] Mermaid pulls a large JS chunk — lazy-load `MapPanel` to cut initial load.
- [ ] Scene images are square (512); consider 16:9 to match the scene panel.
- [ ] Maze rooms share identical descriptions → identical art (faithful, but we
      could vary them deliberately later).
- [ ] Save/restore is in-memory per server process; add durable save files if we
      want saves to survive a backend restart.
- [ ] UI: expose seed / new-game options; small-screen (mobile) layout pass.

## Done (highlights)
- Faithful Python engine (parser + `advent.for` port), validated vs the reference
  port; terminal CLI; full test suite + CI.
- MCP server (tools: new_game, game_command, get_state, get_transcript,
  save_game, restore_game, get_map, get_scene, list_games, end_game).
- Web backend (FastAPI): REST direct-play + Claude-driven `/api/chat`.
- React UI: Classic + Guided modes, scene panel, live Mermaid cave map
  (Here/Nearby/Area/All + Expand), actionable status pills, session persists
  across reloads.
- Local open-weights image generation (SDXL-Turbo working; FLUX/PixArt ready),
  photorealistic high-fantasy style (surface vs. underground), lazy scene cache.
- Docker Desktop stack via `.env` + `advent.sh`; nginx/compose for Athena.
