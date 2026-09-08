# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Per-location scene images: prompts, a pluggable generator, and a cache.

Each location gets one image, generated the first time it is requested and then
cached forever (the "lazy generation" design).  Generation is pluggable: the
default is a dependency-free SVG placeholder, and a real open-weights model
(SDXL-Turbo, FLUX.1-schnell, ...) drops in as a ``generator`` callable that
returns ``(bytes, mimetype)``.  Prompts are built now from each room's
description plus a shared style guide, so swapping in a model needs no other
changes -- it just fills the same cache.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
from pathlib import Path

from .data import GameData

# Photorealistic high fantasy. Most of the game is deep underground, so the
# default look is a vast Moria/Erebor cavern; the handful of surface rooms (which
# the game marks as naturally lit) get an outdoor variant instead. On SDXL each
# style is sent to the second text encoder (its own 77-token budget); on T5
# models it is appended to the scene. Keep each under ~77 tokens.
# These are *modifiers* -- medium, setting, lighting, mood -- NOT scene content.
# The scene text decides what is actually in the picture (a small brick building
# vs. a vast hall); the style must not name architecture or it hijacks the image.
# A style is three look-modifier strings (surface / underground / title). Each
# room picks one by whether it's lit (surface) or deep cave (underground); the
# scene text supplies the content, so styles must NOT name architecture. Keep
# each under ~77 tokens (SDXL's per-encoder budget).
STYLES: dict[str, dict[str, str]] = {
    "photoreal": {
        "surface": ("photorealistic, high fantasy, outdoors in daylight, lush green "
                    "forest, soft natural light, gentle mist, atmospheric, cinematic, "
                    "hyper-detailed, 8k, deserted"),
        "underground": ("photorealistic, high fantasy, deep underground, lit only by "
                        "warm torchlight against near-total darkness, bare rock, damp "
                        "stone, cool shadows, atmospheric haze, cinematic, dramatic, "
                        "hyper-detailed, 8k, deserted"),
        "title": ("photorealistic, epic high fantasy, dramatic cinematic key art, "
                  "moody dusk light, mist and atmosphere, rugged rock, hyper-detailed, "
                  "8k, deserted"),
    },
    "fantasy": {
        "surface": ("digital painting, high fantasy concept art, painterly, luminous "
                    "daylight forest, soft mist, lush, storybook, richly detailed, "
                    "trending on artstation, deserted"),
        "underground": ("digital painting, high fantasy concept art, painterly, vast "
                        "torchlit cavern, deep shadows, glowing embers, dramatic, "
                        "atmospheric, trending on artstation, deserted"),
        "title": ("epic high fantasy concept art, painterly key art, dramatic dusk, "
                  "mist, sweeping vista, trending on artstation, deserted"),
    },
    "anime": {
        "surface": ("anime background art, Studio Ghibli inspired, hand-painted, bright "
                    "daylight forest, soft mist, lush, cel shaded, detailed, deserted"),
        "underground": ("anime background art, Studio Ghibli inspired, hand-painted, "
                        "torchlit cavern, dramatic shadows, glowing light, cel shaded, "
                        "detailed, deserted"),
        "title": ("anime key visual, epic dusk vista, hand-painted, cinematic, deserted"),
    },
    "cartoon": {
        "surface": ("stylized 3d cartoon render, Pixar style, vibrant daylight forest, "
                    "soft shadows, playful, clean shapes, deserted"),
        "underground": ("stylized 3d cartoon render, Pixar style, torchlit cavern, warm "
                        "glow, cozy dramatic lighting, clean shapes, deserted"),
        "title": ("stylized 3d cartoon key art, adventurous dusk vista, playful, deserted"),
    },
    "watercolor": {
        "surface": ("delicate watercolor painting, soft washes, loose ink linework, "
                    "daylight forest, airy, muted palette, deserted"),
        "underground": ("delicate watercolor painting, soft washes, ink linework, "
                        "torchlit cavern, moody, muted palette, deserted"),
        "title": ("watercolor and ink key art, misty dusk vista, loose linework, deserted"),
    },
}

DEFAULT_STYLE = "photoreal"

# Back-compat aliases (the default look's modifiers).
STYLE_SURFACE = STYLES[DEFAULT_STYLE]["surface"]
STYLE_UNDERGROUND = STYLES[DEFAULT_STYLE]["underground"]
STYLE_TITLE = STYLES[DEFAULT_STYLE]["title"]
STYLE_GUIDE = STYLE_UNDERGROUND


def resolve_style(style: str | None) -> str:
    """Normalise a requested style name to a known one (fallback to default)."""
    return style if style in STYLES else DEFAULT_STYLE

# Second-person openings the game uses, stripped so the prompt reads as a scene.
# Each token requires a trailing space so e.g. "in" won't eat the "in" of "inside".
_LEAD = re.compile(
    r"^you(?:'re| are)\s+(?:now\s+|really\s+)?"
    r"(?:(?:standing|sitting|walking|crawling|lying)\s+)?"
    r"(?:(?:at|in|on|inside|atop|near|by|beside)\s+)?"
    r"(?:the\s+)?",
    re.IGNORECASE,
)

_EXT = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


def _scene_subject(text: str) -> str:
    """Turn a room's second-person description into a neutral scene phrase."""
    s = " ".join(text.split()).lower()
    s = _LEAD.sub("", s)          # "you are standing at the end of..." -> "end of..."
    if len(s) > 300:              # keep even a CLIP encoder's scene budget sane
        cut = s.rfind(".", 0, 300)
        s = s[: cut + 1] if cut > 80 else s[:300]
    return s.strip()


# Location 0 is "limbo" before the game places the player -- give it a title card.
_TITLE_SCENE = ("the mouth of a vast colossal cave, a mysterious dark opening in "
                "a rugged rocky hillside at dusk, torchlight glinting within, the "
                "threshold of a grand adventure")


def scene_subject_text(data: GameData, loc: int) -> str:
    """Just the scene (no style), cleaned from the room's description."""
    if loc == 0:
        return _TITLE_SCENE
    text = data.long_desc.get(loc, "")
    if not text or text.startswith(">$<"):
        text = data.short_desc.get(loc) or "a mysterious chamber deep in a colossal cave"
    return _scene_subject(text)


def scene_style(data: GameData, loc: int, style: str = DEFAULT_STYLE) -> str:
    """Look modifiers for a room in the given style.

    Surface (daylit) variant for naturally-lit rooms, cavern variant otherwise;
    location 0 uses the title variant. The game sets the LIGHT condition bit
    (bit 0) on rooms that don't need the lamp -- the surface and a few open
    rooms; everything else is deep cave.
    """
    variants = STYLES[resolve_style(style)]
    if loc == 0:
        return variants["title"]
    lit = bool(data.cond.get(loc, 0) & 1)
    return variants["surface"] if lit else variants["underground"]


def scene_prompt(data: GameData, loc: int, style: str = DEFAULT_STYLE) -> str:
    """The combined prompt (scene then style) for display and single-encoder /
    T5 models. On SDXL the generator instead sends the scene and style to the
    two separate encoders (see ``imagegen``)."""
    return f"{scene_subject_text(data, loc)} — {scene_style(data, loc, style)}"


def _wrap(text: str, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


def placeholder_svg(data: GameData, loc: int) -> tuple[bytes, str]:
    """A dependency-free placeholder: a moody torch-lit stone portal card.

    Suggests a mysterious passage rather than a flat swatch -- a nicer stand-in
    until the real art is generated (and the title card for location 0).
    """
    if loc == 0:
        name, body = "Colossal Cave", "A grand adventure awaits within…"
    else:
        name = (data.short_desc.get(loc) or data.long_desc.get(loc, f"Room {loc}"))
        name = name.split("\n", 1)[0].strip()
        body = " ".join(data.long_desc.get(loc, "").split())
    hue = int(hashlib.sha1(str(loc).encode()).hexdigest(), 16) % 360
    lines = _wrap(body, 40)[:4]
    tspans = "".join(
        f'<tspan x="320" dy="{24 if i else 0}">{_xml(t)}</tspan>' for i, t in enumerate(lines)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
  <defs>
    <radialGradient id="glow" cx="50%" cy="42%" r="65%">
      <stop offset="0" stop-color="hsl({hue},55%,26%)"/>
      <stop offset="0.55" stop-color="hsl({(hue + 20) % 360},45%,11%)"/>
      <stop offset="1" stop-color="#0b0906"/>
    </radialGradient>
    <radialGradient id="ember" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#ffcf7a" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#ffcf7a" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="640" height="400" fill="url(#glow)"/>
  <!-- suggestion of a carved stone archway / passage -->
  <path d="M170 400 V150 a150 150 0 0 1 300 0 V400 Z" fill="#0d0b08" opacity="0.72"/>
  <path d="M170 150 a150 150 0 0 1 300 0" fill="none" stroke="hsl({hue},35%,55%)"
        stroke-width="3" opacity="0.35"/>
  <ellipse cx="320" cy="330" rx="150" ry="60" fill="url(#ember)" opacity="0.5"/>
  <text x="320" y="120" text-anchor="middle" font-family="Georgia, serif" font-size="30"
        fill="#f5e6c8">{_xml(name)}</text>
  <text x="320" y="250" text-anchor="middle" font-family="Georgia, serif" font-size="15"
        fill="#e8dcc4" opacity="0.8">{tspans}</text>
  <text x="320" y="384" text-anchor="middle" font-family="monospace" font-size="11"
        fill="#f5e6c8" opacity="0.5">location {loc} · illustration pending</text>
</svg>"""
    return svg.encode("utf-8"), "image/svg+xml"


def _xml(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class SceneStore:
    """Generate-on-first-request, cache-forever store of location images."""

    def __init__(self, cache_dir: str | Path | None = None, generator=None,
                 style: str = DEFAULT_STYLE):
        base = Path(cache_dir or os.environ.get(
            "ADVENT_SCENE_CACHE", Path.cwd() / "scene-cache"))
        self.style = resolve_style(style)
        self.cache_dir = base / self.style       # one folder of images per style
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.generator = generator or placeholder_svg

    # Prefer real raster art over the SVG placeholder, so a pre-generated PNG
    # wins even if a placeholder was cached earlier during play.
    _LOOKUP_ORDER = ("png", "webp", "jpg", "svg")

    def _find_cached(self, loc: int) -> Path | None:
        for ext in self._LOOKUP_ORDER:
            p = self.cache_dir / f"loc_{loc}.{ext}"
            if p.exists():
                return p
        return None

    def get(self, data: GameData, loc: int) -> dict:
        """Return the image for a location, generating and caching on first use."""
        cached_path = self._find_cached(loc)
        if cached_path is not None:
            content = cached_path.read_bytes()
            mimetype = next(m for m, e in _EXT.items() if e == cached_path.suffix[1:])
            cached = True
        else:
            content, mimetype = self.generator(data, loc)
            ext = _EXT.get(mimetype, "bin")
            (self.cache_dir / f"loc_{loc}.{ext}").write_bytes(content)
            cached = False
        b64 = base64.b64encode(content).decode("ascii")
        return {
            "location": loc,
            "style": self.style,
            "mimetype": mimetype,
            "cached": cached,
            "prompt": scene_prompt(data, loc, self.style),
            "image_base64": b64,
            "data_uri": f"data:{mimetype};base64,{b64}",
        }
