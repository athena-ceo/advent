# Copyright (c) 2026 Athena Decisions Systems SAS.
"""A God's-eye map of Colossal Cave, derived from the parsed travel table.

The travel table *is* a graph: every location's block of entries names, for each
motion keyword, where that motion leads.  We decode those into location-to-
location edges (labelled with the motion words) and render them as a Mermaid
graph or a plain node/edge structure a frontend can draw itself.

Edges that only print a message (no movement) are dropped; conditional motions
(probabilistic or "must be carrying X") are kept but flagged.  The two special
passages that compute their destination at run time -- the plover passage
(99<->100) and the troll bridge (117<->122) -- are reconstructed so the map
stays connected across them.
"""
from __future__ import annotations

from .data import GameData, load_default_data

_MAX_LABEL = 36


def _node_label(data: GameData, loc: int) -> str:
    text = data.short_desc.get(loc) or data.long_desc.get(loc, f"Room {loc}")
    line = text.split("\n", 1)[0].strip()
    if len(line) > _MAX_LABEL:
        line = line[: _MAX_LABEL - 1].rstrip() + "…"
    return line


def build_graph(data: GameData) -> tuple[dict[int, str], list[dict]]:
    """Return ``(nodes, edges)`` for the whole cave.

    ``nodes`` maps location number -> short label.  Each edge is
    ``{"from", "to", "via": [motion words], "conditional": bool, "special": bool}``.
    """
    troll = data.vocab("TROLL", 1)
    nodes = {loc: _node_label(data, loc) for loc in data.long_desc}
    edges: list[dict] = []
    index: dict[tuple[int, int], dict] = {}

    for loc in sorted(data.key):
        kk = data.key[loc]
        while True:
            entry = data.travel[kk]
            enc = abs(entry)
            keyword = enc % 1000
            y = enc // 1000
            cond, dest_code = y // 1000, y % 1000

            dest: int | None = None
            special = False
            if dest_code <= 300:
                dest = dest_code
            elif dest_code <= 500:  # special travel with a computed destination
                special = True
                code = dest_code - 300
                if code == 1:       # plover passage
                    dest = 99 + 100 - loc
                elif code == 3:     # troll bridge
                    dest = data.plac[troll] + data.fixd[troll] - loc
            # dest_code > 500 is message-only: no edge.

            if dest and dest != loc and dest in nodes:
                if keyword == 1:
                    via = "(forced)"
                else:
                    words = data.motion_words(keyword)
                    via = words[0] if words else f"verb{keyword}"
                key = (loc, dest)
                edge = index.get(key)
                if edge is None:
                    edge = {"from": loc, "to": dest, "via": [via],
                            "conditional": cond != 0, "special": special}
                    index[key] = edge
                    edges.append(edge)
                else:
                    if via not in edge["via"]:
                        edge["via"].append(via)
                    # If any route is unconditional/normal, present it that way.
                    edge["conditional"] = edge["conditional"] and cond != 0
                    edge["special"] = edge["special"] and special
            if entry < 0:
                break
            kk += 1

    return nodes, edges


def subgraph(nodes: dict[int, str], edges: list[dict], start: int,
             depth: int) -> tuple[dict[int, str], list[dict]]:
    """Nodes within ``depth`` hops of ``start`` (undirected) and their edges."""
    adjacency: dict[int, set[int]] = {}
    for e in edges:
        adjacency.setdefault(e["from"], set()).add(e["to"])
        adjacency.setdefault(e["to"], set()).add(e["from"])
    reachable = {start}
    frontier = {start}
    for _ in range(max(0, depth)):
        nxt: set[int] = set()
        for node in frontier:
            nxt |= adjacency.get(node, set()) - reachable
        reachable |= nxt
        frontier = nxt
        if not frontier:
            break
    sub_nodes = {loc: nodes[loc] for loc in reachable if loc in nodes}
    sub_edges = [e for e in edges if e["from"] in reachable and e["to"] in reachable]
    return sub_nodes, sub_edges


def _mermaid_escape(text: str) -> str:
    return text.replace('"', "'").replace("|", "/").replace("[", "(").replace("]", ")")


def to_mermaid(nodes: dict[int, str], edges: list[dict], direction: str = "LR",
               highlight: int | None = None) -> str:
    """Render nodes/edges as a Mermaid ``graph`` definition."""
    lines = [f"graph {direction}"]
    for loc in sorted(nodes):
        lines.append(f'  N{loc}["{_mermaid_escape(nodes[loc])}"]')
    for e in edges:
        arrow = "-.->" if e["conditional"] else "-->"
        label = _mermaid_escape("/".join(e["via"]))[:24]
        lines.append(f'  N{e["from"]} {arrow}|{label}| N{e["to"]}')
    if highlight is not None and highlight in nodes:
        lines.append(f"  style N{highlight} fill:#ffd54f,stroke:#333,stroke-width:2px")
    return "\n".join(lines)


# The full graph is derived once and reused.
_cache: tuple[GameData, dict[int, str], list[dict]] | None = None


def cave_graph(data: GameData | None = None) -> tuple[dict[int, str], list[dict]]:
    global _cache
    data = data or load_default_data()
    if _cache is None or _cache[0] is not data:
        nodes, edges = build_graph(data)
        _cache = (data, nodes, edges)
    return _cache[1], _cache[2]


def map_payload(data: GameData, center: int | None = None, depth: int | None = None,
                direction: str = "LR") -> dict:
    """A ready-to-serve map: Mermaid + structured graph, full or a subgraph."""
    nodes, edges = cave_graph(data)
    if center is not None and depth is not None:
        nodes, edges = subgraph(nodes, edges, center, depth)
    return {
        "mermaid": to_mermaid(nodes, edges, direction=direction, highlight=center),
        "graph": {
            "nodes": [{"id": n, "name": name} for n, name in sorted(nodes.items())],
            "edges": edges,
        },
        "node_count": len(nodes),
        "edge_count": len(edges),
        "center": center,
    }
