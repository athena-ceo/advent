# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Pre-generate scene images into the cache with a local open-weights model.

Run this on a machine with a GPU/MPS (your Mac) to fill the scene cache the
Docker app serves. It writes ``loc_<n>.png`` for every location; already-cached
files are skipped unless ``--overwrite`` is given.

    pip install -e "./backend[imagegen]"        # torch + diffusers (big)
    python -m advent.pregen --out ./scene-cache  # SDXL-Turbo by default

Point ``--out`` at the same host folder the compose file mounts
(``ADVENT_SCENE_CACHE_HOST``, default ``./scene-cache``). Use ``--dry-run`` to
print the prompts without loading a model.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .data import load_default_data
from .scene import DEFAULT_STYLE, STYLES, resolve_style, scene_prompt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pre-generate Adventure scene images.")
    p.add_argument("--model", default="stabilityai/sdxl-turbo",
                   help="HuggingFace model id (default: stabilityai/sdxl-turbo)")
    p.add_argument("--out", default="./scene-cache", help="base cache directory")
    p.add_argument("--style", default=DEFAULT_STYLE,
                   help=f"style library (default: {DEFAULT_STYLE}); one of {', '.join(STYLES)}")
    p.add_argument("--steps", type=int, default=None)
    p.add_argument("--guidance", type=float, default=None)
    p.add_argument("--size", type=int, default=None)
    p.add_argument("--only", default=None,
                   help="comma-separated location number(s) to generate, e.g. 130,131,132")
    p.add_argument("--limit", type=int, default=None, help="generate at most N locations")
    p.add_argument("--overwrite", action="store_true", help="regenerate even if cached")
    p.add_argument("--dry-run", action="store_true", help="print prompts, don't generate")
    args = p.parse_args(argv)

    style = resolve_style(args.style)
    data = load_default_data()
    locs = [0] + sorted(data.long_desc)  # 0 = the title card / cave mouth
    if args.only is not None:
        locs = [int(x) for x in str(args.only).split(",") if x.strip() != ""]
    if args.limit is not None:
        locs = locs[: args.limit]

    out = Path(args.out) / style          # one image folder per style
    out.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        for loc in locs:
            print(f"[{loc:3}] {scene_prompt(data, loc, style)[:110]}")
        print(f"\n{len(locs)} locations, style={style}. (dry run -- no images written)")
        return 0

    from .imagegen import DiffusersGenerator

    gen = DiffusersGenerator(args.model, steps=args.steps, guidance=args.guidance,
                             size=args.size, style=style)
    print(f"model={args.model} style={style} device={gen.device} steps={gen.steps} "
          f"guidance={gen.guidance} size={gen.size}")

    made = skipped = 0
    for i, loc in enumerate(locs, 1):
        dest = out / f"loc_{loc}.png"
        if dest.exists() and not args.overwrite:
            skipped += 1
            continue
        content, _ = gen(data, loc)
        dest.write_bytes(content)
        made += 1
        print(f"  [{i}/{len(locs)}] loc {loc} -> {dest.name}", flush=True)

    print(f"\ndone: {made} generated, {skipped} already cached, in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
