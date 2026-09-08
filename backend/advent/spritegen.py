# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Generate transparent sprites for objects/creatures (offline, needs a GPU/MPS).

For each object that gets a sprite, render it on a plain backdrop with the image
model, then cut the backdrop away with `rembg` to get a transparent PNG. The
backend later composites these onto room plates (see ``advent.compositor``).

    pip install -e "./backend[imagegen]"      # adds rembg on top of diffusers
    python -m advent.spritegen --out ./sprite-cache

`--only 8,28` limits to specific object numbers; `--dry-run` prints prompts.
Point `--out` at the folder the backend reads (ADVENT_SPRITE_CACHE).
"""
from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path

from .data import load_default_data
from .scene import DEFAULT_STYLE, STYLES, resolve_style
from .sprites import sprite_objects, sprite_prompt

SPRITE_NEGATIVE = "scene, background, floor, ground, room, landscape, text, watermark, multiple objects"


def _cutout(png_bytes: bytes) -> bytes:
    """Remove the backdrop, returning a transparent RGBA PNG."""
    from PIL import Image
    from rembg import remove

    img = Image.open(BytesIO(png_bytes)).convert("RGBA")
    cut = remove(img)  # rembg returns an RGBA PIL image with the bg alpha=0
    buf = BytesIO()
    cut.save(buf, format="PNG")
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate object/creature sprites.")
    p.add_argument("--model", default="PixArt-alpha/PixArt-Sigma-XL-2-1024-MS")
    p.add_argument("--out", default="./sprite-cache", help="base sprite cache directory")
    p.add_argument("--style", default=DEFAULT_STYLE,
                   help=f"style library (default: {DEFAULT_STYLE}); one of {', '.join(STYLES)}")
    p.add_argument("--steps", type=int, default=None)
    p.add_argument("--guidance", type=float, default=None)
    p.add_argument("--size", type=int, default=None)
    p.add_argument("--only", default=None, help="comma-separated object number(s)")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="print prompts, don't generate")
    args = p.parse_args(argv)

    style = resolve_style(args.style)
    data = load_default_data()
    objs = sprite_objects(data)
    if args.only is not None:
        wanted = {int(x) for x in str(args.only).split(",") if x.strip()}
        objs = [o for o in objs if o in wanted]

    out = Path(args.out) / style          # one sprite folder per style
    out.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        for obj in objs:
            print(f"[obj {obj:3}] {data.object_name(obj)} :: {sprite_prompt(data, obj, style)[:90]}")
        print(f"\n{len(objs)} sprites, style={style}. (dry run -- nothing written)")
        return 0

    from .imagegen import DiffusersGenerator

    gen = DiffusersGenerator(args.model, steps=args.steps, guidance=args.guidance,
                             size=args.size, style=style)
    print(f"model={args.model} style={style} device={gen.device} steps={gen.steps} "
          f"guidance={gen.guidance} size={gen.size} sprites={len(objs)}")

    made = skipped = 0
    for i, obj in enumerate(objs, 1):
        dest = out / f"obj_{obj}.png"
        if dest.exists() and not args.overwrite:
            skipped += 1
            continue
        raw, _ = gen.render(sprite_prompt(data, obj, style), negative=SPRITE_NEGATIVE)
        dest.write_bytes(_cutout(raw))
        made += 1
        print(f"  [{i}/{len(objs)}] obj {obj} ({data.object_name(obj)}) -> {dest.name}",
              flush=True)

    print(f"\ndone: {made} generated, {skipped} already present, in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
