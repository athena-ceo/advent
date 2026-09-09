# Copyright (c) 2026 Athena Decisions Systems SAS.
"""User model, auth, guest-claim, persistence, and reporting (in-memory SQLite)."""
import pytest

from advent.store import AuthError, Store, hash_password, verify_password


@pytest.fixture
def store():
    return Store(":memory:")


def _snap(store, game_id, player_id, score, ended=False):
    store.save_game(game_id, player_id, 1, {"loc": 3}, score=score, max_score=350,
                    turns=score, location=3, ended=ended)


def test_password_hash_roundtrip():
    h = hash_password("hunter2")
    assert h != "hunter2" and verify_password("hunter2", h)
    assert not verify_password("wrong", h)
    assert not verify_password("x", None)


def test_register_login_and_first_user_is_admin(store):
    user, token = store.register("Harley", "secret")
    assert user["name"] == "Harley" and user["registered"] and user["is_admin"]
    assert store.user_for_token(token)["id"] == user["id"]

    # second user is not admin; duplicate name (case-insensitive) rejected
    u2, _ = store.register("Woods", "pass")
    assert not u2["is_admin"]
    with pytest.raises(AuthError):
        store.register("harley", "other")

    # login checks the password
    who, tok2 = store.login("harley", "secret")
    assert who["id"] == user["id"] and store.user_for_token(tok2)
    with pytest.raises(AuthError):
        store.login("Harley", "nope")

    store.logout(token)
    assert store.user_for_token(token) is None


def test_guest_games_are_claimed_on_register(store):
    store.touch_player("guest123")
    _snap(store, "g1", "guest123", 50)
    user, _ = store.register("Alice", "pass", guest_id="guest123")
    # the guest's game now belongs to the account
    assert store.game_player("g1") == user["id"]
    board = store.leaderboard()
    assert board and board[0]["name"] == "Alice" and board[0]["score"] == 50


def test_leaderboard_best_per_player_and_metrics(store):
    a, _ = store.register("Ann", "pass")
    b, _ = store.register("Bob", "pass")
    _snap(store, "a1", a["id"], 30)
    _snap(store, "a2", a["id"], 90, ended=True)   # Ann's best
    _snap(store, "b1", b["id"], 60)
    board = store.leaderboard()
    assert [(e["name"], e["score"]) for e in board] == [("Ann", 90), ("Bob", 60)]

    m = store.metrics()
    assert m["registered_total"] == 2 and m["games_total"] == 3
    assert m["completions"] == 1 and m["top_score"] == 90


def test_admin_queries(store):
    a, _ = store.register("Admin", "pass")
    _snap(store, "g1", a["id"], 10)
    assert any(u["name"] == "Admin" for u in store.list_users())
    assert store.recent_games()[0]["id"] == "g1"
    assert store.reset_leaderboard() == 1
    assert store.leaderboard() == []
    store.delete_user(a["id"])
    assert store.player(a["id"]) is None


def test_session_manager_rehydrates_from_store():
    from advent.session import SessionManager
    st = Store(":memory:")
    mgr = SessionManager(store=st)
    s = mgr.create(seed=1, player_id="p1")
    s.command("no"); mgr.persist(s)
    sid = s.id
    # drop it from memory (as eviction/restart would) -> reattach rebuilds it
    mgr._sessions.clear()
    again = mgr.reattach(sid)
    assert again is not None and again.id == sid
    assert again.state()["location"] == s.state()["location"]
