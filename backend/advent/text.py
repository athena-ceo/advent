# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Presentation helpers.

The game data is ALL CAPS (as the 1977 original stored it). The engine stays
faithful to that; this converts it to normal sentence capitalization purely for
display in the web UI. It is intentionally simple -- lower-case, then capitalize
the start of each sentence -- so it doesn't try to guess proper nouns, beyond a
small keep-list for the iconic shouted magic words.
"""
from __future__ import annotations

import re

# Words kept upper-case even after sentence-casing (shouted magic words, Y2).
_KEEP = {
    "xyzzy": "XYZZY", "plugh": "PLUGH", "plover": "PLOVER", "y2": "Y2",
    "fee": "FEE", "fie": "FIE", "foe": "FOE", "foo": "FOO", "fum": "FUM",
    "ok": "OK",
}


def sentence_case(text: str | None) -> str:
    """ALL-CAPS game text -> normal sentence capitalization (display only)."""
    if not text:
        return text or ""
    out: list[str] = []
    capitalize = True
    for ch in text.lower():
        if capitalize and ch.isalpha():
            out.append(ch.upper())
            capitalize = False
        else:
            out.append(ch)
            if ch in ".!?":
                capitalize = True   # next letter starts a new sentence
    s = "".join(out)
    s = re.sub(r"\bi\b", "I", s)                                    # lone "i" -> "I"
    s = re.sub(r"[A-Za-z0-9]+",
               lambda m: _KEEP.get(m.group(0).lower(), m.group(0)), s)
    return s
