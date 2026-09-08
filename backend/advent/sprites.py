# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Sprites for objects and creatures, and where to place them on a room plate.

Each portable item / creature gets ONE transparent sprite generated offline
(see ``advent.spritegen``); at render time the backend composites the sprites
for whatever the engine says is currently visible onto the base room image
(see ``advent.compositor``).  Cost is linear in (rooms + objects), never
combinatorial.

This module holds the shared bits: which objects get sprites, the generation
prompt, and the placement layout.
"""
from __future__ import annotations

from dataclasses import dataclass

from .data import GameData
from .scene import DEFAULT_STYLE

# The rendering medium per style, so sprites match their room library.
_MEDIUM = {
    "photoreal": "photorealistic, studio product photo",
    "fantasy": "digital painting, painterly concept art",
    "anime": "anime, cel shaded",
    "cartoon": "stylized 3d cartoon, Pixar style",
    "watercolor": "watercolor and ink",
}

# Creatures get drawn large and central; everything else is a smaller "item".
_CREATURE_WORDS = ["SNAKE", "DRAGO", "BIRD", "DWARF", "TROLL", "BEAR"]

# Portable / visually-interesting items worth compositing. Scenery and fixed
# features (grate, door, steps, fissure, chasm, plant, mirror, liquids, the
# vending machine, messages) are left to the base room plate.
_ITEM_WORDS = [
    "KEYS", "LAMP", "CAGE", "ROD", "PILLO", "CLAM", "OYSTE", "MAGAZ", "KNIFE",
    "FOOD", "BOTTL", "AXE", "TABLE", "BATTE",
    # treasures
    "GOLD", "COINS", "CHEST", "EGGS", "TRIDE", "VASE", "EMERA", "PYRAM",
    "PEARL", "RUG", "CHAIN",
]

SPRITE_STYLE = (
    "isolated on a plain flat neutral-grey backdrop, the whole object centered "
    "and fully in frame, soft even studio lighting, high fantasy, highly detailed, "
    "sharp focus, no scenery, no background, no floor"
)


@dataclass(frozen=True)
class Placement:
    """Where/how big a sprite sits on the plate, as fractions of the image."""
    cx: float      # centre x (0..1)
    bottom: float  # bottom edge y (0..1)
    height: float  # sprite height as a fraction of the plate height


def _reverse(data: GameData) -> dict[int, str]:
    """obj number -> the 5-char vocab word we resolved it from (for categories)."""
    cache = data.__dict__.get("_sprite_words")
    if cache is None:
        cache = {}
        for word in _CREATURE_WORDS + _ITEM_WORDS:
            try:
                cache[data.vocab(word, 1)] = word
            except KeyError:
                pass
        data.__dict__["_sprite_words"] = cache
    return cache


def sprite_objects(data: GameData) -> list[int]:
    """Object numbers that get a sprite, in a stable order."""
    return sorted(_reverse(data))


def is_creature(data: GameData, obj: int) -> bool:
    return _reverse(data).get(obj) in _CREATURE_WORDS


def has_sprite(data: GameData, obj: int) -> bool:
    return obj in _reverse(data)


def sprite_prompt(data: GameData, obj: int, style: str = DEFAULT_STYLE) -> str:
    """Prompt for generating one object's sprite, in the given style."""
    name = data.object_name(obj).lower()
    kind = "a fearsome creature," if is_creature(data, obj) else "a single game object,"
    medium = _MEDIUM.get(style, _MEDIUM[DEFAULT_STYLE])
    return f"{name}, {kind} {medium}, {SPRITE_STYLE}"


def layout(data: GameData, present: list[int]) -> list[tuple[int, Placement]]:
    """Assign each present object a Placement.

    Creatures go large and centre-stage; items are spread along a low shelf so
    several can share a room without stacking on the exact same spot.
    """
    creatures = [o for o in present if is_creature(data, o)]
    items = [o for o in present if not is_creature(data, o)]
    out: list[tuple[int, Placement]] = []

    for i, obj in enumerate(creatures):
        # nudge multiple creatures apart around centre
        offset = 0.0 if len(creatures) == 1 else (i / (len(creatures) - 1) - 0.5) * 0.4
        out.append((obj, Placement(cx=0.5 + offset, bottom=0.96, height=0.55)))

    n = len(items)
    for i, obj in enumerate(items):
        # spread across the lower third, alternating a little in depth/size
        cx = (i + 1) / (n + 1) if n else 0.5
        bottom = 0.90 if i % 2 == 0 else 0.82
        out.append((obj, Placement(cx=cx, bottom=bottom, height=0.24)))
    return out
