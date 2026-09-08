# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Tests for the cave map and scene-image tools."""
from __future__ import annotations

import pytest

from advent import cavemap
from advent.data import load_default_data
from advent.scene import (
    STYLE_SURFACE,
    STYLE_UNDERGROUND,
    SceneStore,
    scene_prompt,
    scene_style,
)


@pytest.fixture(scope="module")
def data():
    return load_default_data()


def test_cave_graph_shape(data):
    nodes, edges = cavemap.build_graph(data)
    assert len(nodes) == 140
    assert edges
    assert all(e["from"] in nodes and e["to"] in nodes for e in edges)


def test_map_is_connected_across_special_passages(data):
    nodes, edges = cavemap.cave_graph(data)
    reach, _ = cavemap.subgraph(nodes, edges, 1, depth=999)
    # From the start you can reach almost everything, including the far side of
    # the troll bridge (117/122) and the plover passage (99/100).
    assert len(reach) >= 138
    for loc in (100, 117, 122, 130):
        assert loc in reach


def test_subgraph_radius(data):
    nodes, edges = cavemap.cave_graph(data)
    sub_nodes, sub_edges = cavemap.subgraph(nodes, edges, 1, depth=1)
    assert 1 in sub_nodes
    assert 2 <= len(sub_nodes) < len(nodes)


def test_mermaid_renders(data):
    nodes, edges = cavemap.cave_graph(data)
    m = cavemap.to_mermaid(nodes, edges, direction="LR", highlight=1)
    assert m.startswith("graph LR")
    assert 'N1["' in m
    assert "-->" in m and "-.->" in m  # normal and conditional edges
    assert "style N1" in m


def test_scene_prompt_and_store(tmp_path, data):
    # Surface rooms (lit) get the daylight style; deep rooms get the cavern one.
    assert STYLE_SURFACE in scene_prompt(data, 1)          # room 1 = surface
    assert STYLE_UNDERGROUND in scene_prompt(data, 19)     # room 19 = deep cave
    assert STYLE_SURFACE in scene_style(data, 1)  # look + shared world bible

    store = SceneStore(cache_dir=tmp_path)
    first = store.get(data, 3)
    assert first["cached"] is False
    assert first["data_uri"].startswith("data:image/svg+xml;base64,")
    assert first["mimetype"] == "image/svg+xml"
    assert scene_style(data, 3) in first["prompt"]

    # A cached file now exists (in the per-style subfolder) and is served again.
    assert (store.cache_dir / "loc_3.svg").exists()
    assert store.cache_dir.name == "photoreal"
    second = store.get(data, 3)
    assert second["cached"] is True
    assert second["image_base64"] == first["image_base64"]


def test_pluggable_generator(tmp_path, data):
    def fake_png(_data, _loc):
        return b"\x89PNG_stub", "image/png"

    store = SceneStore(cache_dir=tmp_path, generator=fake_png)
    result = store.get(data, 5)
    assert result["mimetype"] == "image/png"
    assert (store.cache_dir / "loc_5.png").exists()


def test_map_and_scene_mcp_tools():
    pytest.importorskip("mcp")
    from advent import mcp_server as srv

    full = srv.get_map()
    assert full["node_count"] == 140 and full["mermaid"].startswith("graph")

    r = srv.new_game(seed=1)
    sid = r["session_id"]
    srv.game_command(sid, "no")
    srv.game_command(sid, "enter")

    focused = srv.get_map(session_id=sid, depth=1)
    assert focused["center"] == 3 and focused["node_count"] < 140

    scene = srv.get_scene(session_id=sid)
    assert scene["location"] == 3 and scene["data_uri"].startswith("data:")
    assert "error" in srv.get_scene()
    srv.end_game(sid)
