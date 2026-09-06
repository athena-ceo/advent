# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Parser for ``advent.dat``, the Colossal Cave Adventure database.

The database is divided into 12 numbered sections, each introduced by a line
containing just the section number and terminated by a line containing ``-1``.
Section 0 ends the database.  The format is documented in the header comments
of ``advent.for`` (sections 1-12).  This module turns the raw file into a
:class:`GameData` structure that the engine consumes directly, preserving the
original numbering and encodings (notably the flat ``travel`` array and the
``key`` index into it) so the engine can mirror the FORTRAN faithfully.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DATA_FILE = Path(__file__).with_name("advent.dat")

# Message sections store one-to-many lines of text keyed by a number; multiple
# consecutive lines sharing that number form a single (multi-line) message.
_MESSAGE_SECTIONS = {1, 2, 5, 6, 10, 12}


@dataclass
class GameData:
    """Parsed, immutable game database (the "content" of Adventure)."""

    # Section 1 / 2: location descriptions, keyed by location number.
    long_desc: dict[int, str] = field(default_factory=dict)
    short_desc: dict[int, str] = field(default_factory=dict)

    # Section 3: travel table.  ``travel`` is a flat 1-indexed array of encoded
    # entries (newloc*1000 + motion-keyword), the last entry for each location
    # negated; ``key[loc]`` is the index of the first entry for that location.
    travel: list[int] = field(default_factory=lambda: [0])  # index 0 unused
    key: dict[int, int] = field(default_factory=dict)

    # Section 4: vocabulary.  Parallel lists preserving file order; ``num`` is
    # the KTAB value (num//1000 is the word type), ``word`` the 5-char keyword.
    vocab_num: list[int] = field(default_factory=list)
    vocab_word: list[str] = field(default_factory=list)

    # Section 5: object messages.  ``inventory[obj]`` is the "in room" message;
    # ``prop_msg[obj][n]`` is the description for property state n (None if the
    # message is ">$<", meaning print nothing).  ``has_text`` marks objects
    # that own any section-5 text (used to init treasure props to -1).
    inventory: dict[int, str] = field(default_factory=dict)
    prop_msg: dict[int, list[str | None]] = field(default_factory=dict)
    has_text: set[int] = field(default_factory=set)

    # Section 6 / 12: arbitrary ("random") and magic messages.
    rtext: dict[int, str] = field(default_factory=dict)
    mtext: dict[int, str] = field(default_factory=dict)

    # Section 7: initial object locations.  plac = first/primary location,
    # fixd = -1 (immovable) or second location (two-placed) or 0 (movable).
    plac: dict[int, int] = field(default_factory=dict)
    fixd: dict[int, int] = field(default_factory=dict)

    # Section 8: default message (section 6 index) for each action verb.
    actspk: dict[int, int] = field(default_factory=dict)

    # Section 9: per-location condition bits.
    cond: dict[int, int] = field(default_factory=dict)

    # Section 10: player-class (scoring) messages, in ascending threshold order.
    ctext: list[str] = field(default_factory=list)
    cval: list[int] = field(default_factory=list)

    # Section 11: hints. hints[n] = (turns, points, question_msg, hint_msg).
    hints: dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    hntmax: int = 0

    # ---- vocabulary lookup ------------------------------------------------

    def vocab(self, word: str, init: int) -> int:
        """Look up ``word`` in the vocabulary (mirrors FORTRAN ``VOCAB``).

        ``init`` selects the word type to consider: 0=motion, 1=object,
        2=action, 3=special; for these the KTAB value is returned mod 1000.
        ``init == -1`` matches any type and returns the full KTAB value, or
        -1 if the word is not found.
        """
        if word is None:
            return -1
        w = word[:5].upper()
        for num, atab in zip(self.vocab_num, self.vocab_word):
            if init >= 0 and num // 1000 != init:
                continue
            if atab == w:
                return num % 1000 if init >= 0 else num
        if init >= 0:
            raise KeyError(f"required vocabulary word not found: {word!r}")
        return -1


def _split_message_line(line: str) -> tuple[int, str]:
    """Split a message record ``NUMBER<TAB>TEXT`` on its first tab only."""
    num_str, _, text = line.partition("\t")
    return int(num_str), text


def _first_token(line: str) -> str:
    """First whitespace/tab-delimited token of a line ("" if blank)."""
    stripped = line.strip()
    if not stripped:
        return ""
    return stripped.split(None, 1)[0]


def _is_terminator(line: str) -> bool:
    """A section ends at a record whose first token is ``-1`` (e.g. "-1<TAB>END")."""
    return _first_token(line) == "-1"


def parse(text: str) -> GameData:
    """Parse the full contents of an ``advent.dat`` file into a GameData."""
    data = GameData()
    lines = text.split("\n")
    i = 0
    n = len(lines)

    def next_line() -> str | None:
        nonlocal i
        if i >= n:
            return None
        line = lines[i]
        i += 1
        return line

    while True:
        header = next_line()
        if header is None:
            break
        if header.strip() == "":
            continue
        sect = int(_first_token(header))
        if sect == 0:
            break
        if sect in _MESSAGE_SECTIONS:
            _parse_message_section(sect, data, next_line)
        elif sect == 3:
            _parse_travel(data, next_line)
        elif sect == 4:
            _parse_vocab(data, next_line)
        elif sect == 7:
            _parse_object_locations(data, next_line)
        elif sect == 8:
            _parse_actspk(data, next_line)
        elif sect == 9:
            _parse_cond(data, next_line)
        elif sect == 11:
            _parse_hints(data, next_line)
        else:  # pragma: no cover - guarded by the known section set above
            raise ValueError(f"invalid section number in database: {sect}")

    return data


def _parse_message_section(sect: int, data: GameData, next_line) -> None:
    # Accumulate consecutive lines that share the same leading number into one
    # message.  In section 5, numbers 1..99 introduce an object (inventory
    # message) while 0/100/200/... are property messages for the current object.
    cur_num: int | None = None
    cur_lines: list[str] = []
    cur_obj: int | None = None  # section 5 only

    def flush() -> None:
        nonlocal cur_num, cur_lines
        if cur_num is None:
            return
        message = "\n".join(cur_lines)
        _store_message(sect, cur_num, message, data, cur_obj)
        cur_num, cur_lines = None, []

    while True:
        line = next_line()
        if line is None or _is_terminator(line):
            break
        if line.strip() == "":
            continue
        num, txt = _split_message_line(line)
        if sect == 5 and 1 <= num <= 99:
            # New object: flush any pending message, then start its inventory
            # message.  Property messages that follow attach to this object.
            flush()
            cur_obj = num
            data.has_text.add(num)
            cur_num, cur_lines = num, [txt]
            flush()
            continue
        if num == cur_num:
            cur_lines.append(txt)
        else:
            flush()
            cur_num, cur_lines = num, [txt]
    flush()


def _store_message(sect: int, num: int, message: str, data: GameData, cur_obj) -> None:
    if sect == 1:
        data.long_desc[num] = message
    elif sect == 2:
        data.short_desc[num] = message
    elif sect == 5:
        if 1 <= num <= 99:
            data.inventory[num] = message
        else:  # property message for the current object; prop index = num//100
            prop = num // 100
            props = data.prop_msg.setdefault(cur_obj, [])
            while len(props) <= prop:
                props.append(None)
            props[prop] = None if message.startswith(">$<") else message
            data.has_text.add(cur_obj)
    elif sect == 6:
        data.rtext[num] = message
    elif sect == 10:
        data.ctext.append(message)
        data.cval.append(num)
    elif sect == 12:
        data.mtext[num] = message


def _tokens(line: str) -> list[int]:
    return [int(tok) for tok in line.split()]


def _parse_travel(data: GameData, next_line) -> None:
    travel = data.travel
    key = data.key
    while True:
        line = next_line()
        if line is None or _is_terminator(line):
            break
        if line.strip() == "":
            continue
        nums = _tokens(line)
        loc = nums[0]
        if loc == 0:  # F40-bug kluge line; skip
            continue
        newloc = nums[1]
        motions = nums[2:]
        # A location's records are contiguous; the first one opens its block.
        # Continuation records simply append more entries.  The FORTRAN negates
        # each record's last entry and un-negates on continuation, so that only
        # each location's final entry stays negated -- we defer that to
        # ``_finalize_travel`` and keep every entry positive here.
        if loc not in key:
            key[loc] = len(travel)
        for m in motions:
            if m == 0:
                break
            travel.append(newloc * 1000 + m)


def _parse_vocab(data: GameData, next_line) -> None:
    while True:
        line = next_line()
        if line is None:
            break
        stripped = line.strip()
        if stripped == "":
            continue
        num_str, _, word = line.partition("\t")
        num = int(num_str)
        if num == 0:  # F40-bug kluge line; skip
            continue
        if num == -1:
            break
        data.vocab_num.append(num)
        data.vocab_word.append(word.strip().upper())


def _parse_object_locations(data: GameData, next_line) -> None:
    while True:
        line = next_line()
        if line is None or _is_terminator(line):
            break
        if line.strip() == "":
            continue
        nums = _tokens(line)
        obj = nums[0]
        data.plac[obj] = nums[1] if len(nums) > 1 else 0
        data.fixd[obj] = nums[2] if len(nums) > 2 else 0


def _parse_actspk(data: GameData, next_line) -> None:
    while True:
        line = next_line()
        if line is None or _is_terminator(line):
            break
        if line.strip() == "":
            continue
        nums = _tokens(line)
        data.actspk[nums[0]] = nums[1] if len(nums) > 1 else 0


def _parse_cond(data: GameData, next_line) -> None:
    while True:
        line = next_line()
        if line is None or _is_terminator(line):
            break
        if line.strip() == "":
            continue
        nums = _tokens(line)
        bit = nums[0]
        for loc in nums[1:]:
            if loc == 0:
                break
            data.cond[loc] = data.cond.get(loc, 0) + (1 << bit)


def _parse_hints(data: GameData, next_line) -> None:
    while True:
        line = next_line()
        if line is None or _is_terminator(line):
            break
        if line.strip() == "":
            continue
        nums = _tokens(line)
        k = nums[0]
        if k == 0:  # F40-bug kluge line; skip
            continue
        data.hints[k] = (nums[1], nums[2], nums[3], nums[4])
        data.hntmax = max(data.hntmax, k)


def _finalize_travel(data: GameData) -> None:
    """Negate the final travel entry of each location's contiguous block.

    ``_parse_travel`` appends entries and un-negates on continuation; the block
    boundaries are exactly where ``key`` values start, so the entry immediately
    before each block start (and the very last entry) is a block terminator.
    """
    travel = data.travel
    starts = sorted(data.key.values())
    for start in starts:
        if start - 1 >= 1 and travel[start - 1] > 0:
            travel[start - 1] = -travel[start - 1]
    if travel and travel[-1] > 0:
        travel[-1] = -travel[-1]


def load_default_data() -> GameData:
    """Load and parse the bundled ``advent.dat``."""
    data = parse(DATA_FILE.read_text())
    _finalize_travel(data)
    return data


def parse_file(path: str | Path) -> GameData:
    data = parse(Path(path).read_text())
    _finalize_travel(data)
    return data
