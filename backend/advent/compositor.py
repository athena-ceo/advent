# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Composite object/creature sprites onto a base room plate.

Given the room and the set of objects the engine says are currently visible,
paste their transparent sprites onto the base image and cache the result. The
cache key includes a hash of the base plate, so regenerating a room's art
invalidates its composites automatically. If a sprite file is missing (not yet
generated) it's simply skipped, so this degrades gracefully to base-only art.
"""
from __future__ import annotations

import base64
import hashlib
from io import BytesIO
from pathlib import Path

from . import sprites
from .data import GameData
from .scene import SceneStore

_RASTER = {"image/png", "image/jpeg", "image/webp"}


class SceneComposer:
    def __init__(self, scene_store: SceneStore, sprite_dir: str | Path,
                 composite_dir: str | Path | None = None):
        self.scenes = scene_store
        style = scene_store.style
        # Sprites and composites live in per-style subfolders, matching the
        # scene store, so each library stays self-consistent.
        self.sprite_dir = Path(sprite_dir) / style
        base_comp = Path(composite_dir) if composite_dir else \
            self.scenes.cache_dir.parent.parent / "composite-cache"
        self.composite_dir = base_comp / style
        self.composite_dir.mkdir(parents=True, exist_ok=True)

    def _sprite_path(self, obj: int) -> Path:
        return self.sprite_dir / f"obj_{obj}.png"

    def render(self, data: GameData, loc: int, present: list[int]) -> dict:
        """Return the scene for a room with the currently-visible sprites on it."""
        base = self.scenes.get(data, loc)
        present = [o for o in present
                   if sprites.has_sprite(data, o) and self._sprite_path(o).exists()]
        if not present or base["mimetype"] not in _RASTER:
            return base  # nothing to add, or base is the SVG placeholder

        base_bytes = base64.b64decode(base["image_base64"])
        digest = hashlib.sha1(base_bytes).hexdigest()[:8]
        key = f"{loc}_{digest}_" + "-".join(str(o) for o in sorted(present))
        dest = self.composite_dir / f"{key}.png"
        if dest.exists():
            content = dest.read_bytes()
        else:
            content = self._compose(data, base_bytes, present)
            dest.write_bytes(content)

        b64 = base64.b64encode(content).decode("ascii")
        return {**base, "mimetype": "image/png", "image_base64": b64,
                "data_uri": f"data:image/png;base64,{b64}",
                "composited": True, "objects": present}

    def _compose(self, data: GameData, base_bytes: bytes, present: list[int]) -> bytes:
        from PIL import Image

        bg = Image.open(BytesIO(base_bytes)).convert("RGBA")
        w, h = bg.size
        for obj, place in sprites.layout(data, present):
            try:
                sprite = Image.open(self._sprite_path(obj)).convert("RGBA")
            except Exception:
                continue
            target_h = max(1, int(place.height * h))
            scale = target_h / sprite.height
            target_w = max(1, int(sprite.width * scale))
            sprite = sprite.resize((target_w, target_h), Image.LANCZOS)
            x = int(place.cx * w - target_w / 2)
            y = int(place.bottom * h - target_h)
            bg.alpha_composite(sprite, (max(0, min(x, w - target_w)),
                                        max(0, min(y, h - target_h))))
        out = BytesIO()
        bg.convert("RGB").save(out, format="PNG")
        return out.getvalue()
