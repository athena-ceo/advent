# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Display-layer text prettification."""
from advent.text import sentence_case


def test_sentence_case_basic():
    assert sentence_case("YOU ARE IN A MAZE.") == "You are in a maze."


def test_multi_sentence_and_newlines():
    src = "A ROAD.\nAROUND YOU IS A FOREST AND\nDOWN A GULLY."
    # New sentence after '.', but a wrapped continuation line stays lower-case.
    assert sentence_case(src) == "A road.\nAround you is a forest and\ndown a gully."


def test_keeps_magic_words_and_ok_and_i():
    assert sentence_case("OK") == "OK"
    assert sentence_case("YOU'RE AT 'Y2'.") == "You're at 'Y2'."
    assert sentence_case('SAYS "MAGIC WORD XYZZY".') == 'Says "magic word XYZZY".'
    assert sentence_case("NOW I SEE.") == "Now I see."


def test_empty():
    assert sentence_case("") == ""
    assert sentence_case(None) == ""
