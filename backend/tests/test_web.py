# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Tests for the REST backend (direct play, map, scene, save/restore, chat gate)."""
from __future__ import annotations

import os

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from advent.web import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_direct_play_flow(client):
    sid = client.post("/api/games", json={"seed": 1}).json()["session_id"]
    for cmd in ["no", "enter", "take lamp"]:
        r = client.post(f"/api/games/{sid}/command", json={"command": cmd}).json()
    assert r["state"]["location"] == 3
    assert any(o["name"].lower() == "brass lantern" for o in r["state"]["inventory"])

    assert client.get(f"/api/games/{sid}/state").json()["location"] == 3
    assert client.get(f"/api/games/{sid}/transcript").json()["transcript"]

    scene = client.get(f"/api/games/{sid}/scene").json()
    assert scene["location"] == 3 and scene["data_uri"].startswith("data:")

    m = client.get(f"/api/games/{sid}/map", params={"depth": 1}).json()
    assert m["center"] == 3 and m["node_count"] >= 2


def test_save_and_restore(client):
    sid = client.post("/api/games", json={"seed": 1}).json()["session_id"]
    for cmd in ["no", "enter", "take lamp"]:
        client.post(f"/api/games/{sid}/command", json={"command": cmd})
    save_id = client.post(f"/api/games/{sid}/save").json()["save_id"]
    r = client.post("/api/restore", json={"save_id": save_id}).json()
    assert r["state"]["location"] == 3
    assert any(o["name"].lower() == "brass lantern" for o in r["state"]["inventory"])


def test_unknown_session_is_404(client):
    assert client.get("/api/games/nope/state").status_code == 404


def test_chat_requires_api_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    sid = client.post("/api/games", json={"seed": 1}).json()["session_id"]
    r = client.post(f"/api/games/{sid}/chat", json={"message": "look around"})
    assert r.status_code == 503
