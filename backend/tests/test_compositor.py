# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Sprite placement + compositing (dummy images; no model needed)."""
from io import BytesIO

import pytest

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from advent import sprites  # noqa: E402
from advent.compositor import SceneComposer  # noqa: E402
from advent.data import load_default_data  # noqa: E402
from advent.scene import SceneStore  # noqa: E402


def _png(w, h, color, mode="RGB") -> bytes:
    buf = BytesIO()
    Image.new(mode, (w, h), color).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def data():
    return load_default_data()


def test_layout_creatures_bigger_than_items(data):
    snake = data.vocab("SNAKE", 1)
    keys = data.vocab("KEYS", 1)
    assert sprites.is_creature(data, snake)
    assert not sprites.is_creature(data, keys)
    placed = dict(sprites.layout(data, [snake, keys]))
    assert placed[snake].height > placed[keys].height


def test_composite_and_cache(tmp_path, data):
    scene_dir = tmp_path / "scenes"; scene_dir.mkdir()
    sprite_dir = tmp_path / "sprites"; sprite_dir.mkdir()
    (scene_dir / "loc_5.png").write_bytes(_png(640, 400, (20, 20, 20)))
    keys = data.vocab("KEYS", 1)
    sprite_dir.joinpath(f"obj_{keys}.png").write_bytes(_png(100, 100, (255, 0, 0, 255), "RGBA"))

    comp = SceneComposer(SceneStore(cache_dir=scene_dir), sprite_dir,
                         composite_dir=tmp_path / "composite")
    r = comp.render(data, 5, [keys])
    assert r.get("composited") and r["objects"] == [keys]
    assert r["mimetype"] == "image/png" and r["data_uri"].startswith("data:image/png")
    assert list((tmp_path / "composite").glob("5_*.png"))  # cached

    # No visible objects -> the base plate is returned untouched.
    assert not comp.render(data, 5, []).get("composited")

    # An object without a generated sprite file is skipped (degrades gracefully).
    assert not comp.render(data, 5, [data.vocab("LAMP", 1)]).get("composited")
