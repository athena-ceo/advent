# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Parser tests.

Two kinds of checks:

* *Structural* — the parsed database matches the size limits documented in the
  header of ``advent.for`` (a self-contained sanity check).
* *Cross-validation* — every room description, object message, and arbitrary
  message matches Brandon Rhodes' independently-written ``adventure`` package,
  which parses the identical ``advent.dat``.  This is our fidelity oracle for
  the *content*; gameplay fidelity is covered by ``test_walkthrough``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from advent.data import load_default_data


def _norm(text: str | None) -> str:
    """Normalise for comparison: drop trailing newlines, expand tabs.

    ``>$<`` is the database's "print nothing" sentinel; the reference renders it
    as an empty string, and our parser stores ``None``.  Both normalise to "".
    """
    if text is None:
        return ""
    if text.startswith(">$<"):
        return ""
    return "\n".join(line.rstrip() for line in text.expandtabs().rstrip("\n").split("\n"))


@pytest.fixture(scope="module")
def data():
    return load_default_data()


@pytest.fixture(scope="module")
def ref():
    ad = pytest.importorskip("adventure.data")
    refdata = ad.Data()
    with open(Path(ad.__file__).with_name("advent.dat")) as f:
        ad.parse(refdata, f)
    return refdata


# --- structural checks (documented limits from advent.for) -----------------

def test_section_counts(data):
    assert len(data.long_desc) == 140          # LOCSIZ 150, 140 used
    assert len(data.short_desc) == 65
    assert len(data.travel) - 1 == 741         # TRVSIZ 750
    assert len(data.vocab_num) == 295          # TABSIZ 300
    assert len(data.rtext) == 198              # RTXSIZ 205
    assert len(data.mtext) == 32               # MAGSIZ 35
    assert data.cval == [35, 100, 130, 200, 250, 300, 330, 349, 9999]
    assert data.hntmax == 9


def test_travel_blocks_terminated(data):
    """Every location's travel block ends with exactly one negated entry."""
    starts = sorted(data.key.values())
    bounds = starts[1:] + [len(data.travel)]
    for start, end in zip(starts, bounds):
        block = data.travel[start:end]
        assert block, "empty travel block"
        assert all(e > 0 for e in block[:-1]), "interior entry negated"
        assert block[-1] < 0, "block not terminated by a negated entry"


def test_vocab_types(data):
    assert data.vocab("ROAD", 0) == 2       # motion
    assert data.vocab("LAMP", 1) == 2       # object
    assert data.vocab("TAKE", 2) == 1       # action verb "CARRY/TAKE"
    assert data.vocab("XYZZY", -1) == 62    # special word, full value
    assert data.vocab("NOTAWORD", -1) == -1


# --- cross-validation against the reference port ---------------------------

def test_room_descriptions_match_reference(data, ref):
    for n, room in ref.rooms.items():
        if n not in data.long_desc:
            continue
        assert _norm(data.long_desc[n]) == _norm(room.long_description), f"long desc {n}"
        assert _norm(data.short_desc.get(n)) == _norm(room.short_description), f"short desc {n}"


def test_object_messages_match_reference(data, ref):
    for n, obj in ref.objects.items():
        if n not in data.inventory and n not in data.prop_msg:
            continue
        if obj.inventory_message:
            assert _norm(data.inventory.get(n)) == _norm(obj.inventory_message), f"inv {n}"
        for prop, msg in obj.messages.items():
            mine = data.prop_msg.get(n, [])
            assert 0 <= prop < len(mine), f"missing prop {prop} of obj {n}"
            # ``None`` (our ">$<" sentinel) and "" (the reference's) both normalise
            # to "", so silent property messages compare equal.
            assert _norm(mine[prop]) == _norm(str(msg)), f"obj {n} prop {prop}"


def test_arbitrary_messages_match_reference(data, ref):
    for n, msg in ref.messages.items():
        assert _norm(data.rtext.get(n)) == _norm(str(msg)), f"rtext {n}"


def test_object_placement_match_reference(data, ref):
    for n, obj in ref.objects.items():
        if n not in data.plac:
            continue
        # Compare real (positive) starting rooms; "room 0" means the object
        # starts nowhere and is represented differently by each parser.
        ref_rooms = sorted(r.n for r in obj.starting_rooms if r.n > 0)
        mine = [data.plac[n]] + ([data.fixd[n]] if data.fixd[n] > 0 else [])
        assert sorted(x for x in mine if x > 0) == ref_rooms, f"placement obj {n}"
