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

# Photorealistic high fantasy -- Myst, but more fantastical. On SDXL this is sent
# to the *second* text encoder (its own 77-token budget), so it applies in full
# to every room without crowding out the scene; on other models it is appended
# to the scene. Keep it under ~77 tokens.
STYLE_GUIDE = (
    "photorealistic high fantasy in the spirit of Myst but more fantastical, "
    "a still uninhabited cinematic establishing shot, ancient hand-built "
    "stonework meeting an otherworldly landscape, volumetric light, drifting "
    "mist, weathered textures, physically based rendering, ray-traced global "
    "illumination, hyper-detailed, 8k, deserted and empty, no signage"
)

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


def scene_subject_text(data: GameData, loc: int) -> str:
    """Just the scene (no style), cleaned from the room's description."""
    text = data.long_desc.get(loc, "")
    if not text or text.startswith(">$<"):
        text = data.short_desc.get(loc) or "a mysterious chamber deep in a colossal cave"
    return _scene_subject(text)


def scene_prompt(data: GameData, loc: int) -> str:
    """The combined prompt (scene then style) for display and single-encoder /
    T5 models. On SDXL the generator instead sends the scene and style to the
    two separate encoders (see ``imagegen``)."""
    return f"{scene_subject_text(data, loc)} — {STYLE_GUIDE}"


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
    """A dependency-free placeholder image: a captioned, tinted card."""
    name = (data.short_desc.get(loc) or data.long_desc.get(loc, f"Room {loc}"))
    name = name.split("\n", 1)[0].strip()
    hue = int(hashlib.sha1(str(loc).encode()).hexdigest(), 16) % 360
    body = " ".join(data.long_desc.get(loc, "").split())
    lines = _wrap(body, 46)[:6]
    tspans = "".join(
        f'<tspan x="40" dy="{28 if i else 0}">{_xml(t)}</tspan>'
        for i, t in enumerate(lines)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="hsl({hue},45%,28%)"/>
    <stop offset="1" stop-color="hsl({(hue + 40) % 360},50%,12%)"/>
  </linearGradient></defs>
  <rect width="640" height="400" fill="url(#g)"/>
  <rect x="16" y="16" width="608" height="368" fill="none" stroke="hsl({hue},40%,70%)" stroke-width="2" opacity="0.5"/>
  <text x="40" y="70" font-family="Georgia, serif" font-size="26" fill="#f5f0e6">{_xml(name)}</text>
  <text x="40" y="130" font-family="Georgia, serif" font-size="17" fill="#e8e0d0" opacity="0.85">{tspans}</text>
  <text x="40" y="372" font-family="monospace" font-size="12" fill="#f5f0e6" opacity="0.6">location {loc} · placeholder — AI art pending</text>
</svg>"""
    return svg.encode("utf-8"), "image/svg+xml"


def _xml(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class SceneStore:
    """Generate-on-first-request, cache-forever store of location images."""

    def __init__(self, cache_dir: str | Path | None = None, generator=None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "ADVENT_SCENE_CACHE", Path.cwd() / "scene-cache"))
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
            "mimetype": mimetype,
            "cached": cached,
            "prompt": scene_prompt(data, loc),
            "image_base64": b64,
            "data_uri": f"data:{mimetype};base64,{b64}",
        }
