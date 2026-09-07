# Copyright (c) 2026 Athena Decisions Systems SAS.
"""The Adventure engine: a faithful Python port of ``advent.for``.

The FORTRAN original is one large routine wired together with ``GOTO``s.  We
preserve that control flow exactly -- each numbered label becomes a small
method that returns the name of the next label -- because the game's behaviour
lives in those jumps.  A dispatch loop (:meth:`_drive`) runs label to label
until the game ends.  Statement numbers from ``advent.for`` appear in comments
and method names (``_l2000`` == FORTRAN label 2000) so the two can be read side
by side.

State is plain attributes on the instance and is fully serialisable, so the
engine can be driven a command at a time by a CLI, a web backend, or an MCP
tool server, and its state inspected or saved between turns.
"""
from __future__ import annotations

from .data import GameData, load_default_data
from .rng import Rng


class _GameOver(Exception):
    """Raised internally to unwind out of the dispatch loop when the game ends."""


def _div(a: int, b: int) -> int:
    """Integer division truncated toward zero (FORTRAN semantics)."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _mod(a: int, b: int) -> int:
    """Remainder with the sign of the dividend (FORTRAN ``MOD``)."""
    return a - _div(a, b) * b


class Game:
    MAXTRS = 79  # objects 50..79 are treasures

    def __init__(self, data: GameData | None = None, seed: int | None = None):
        self.data = data or load_default_data()
        self.rng = Rng(seed)
        self._read_line = None
        self._write = None
        self.transcript: list[str] = []
        self._build_dispatch()
        self._init_state()

    # ------------------------------------------------------------------ setup

    def _v(self, word: str, init: int) -> int:
        return self.data.vocab(word, init)

    def _init_state(self) -> None:
        d = self.data
        maxloc = 300
        # Object arrays (1..100); index 0 kept as a harmless slot -- the FORTRAN
        # references the never-assigned mnemonic SPICES, which defaults to 0.
        self.place = [0] * 101
        self.fixed = [0] * 101
        self.prop = [0] * 101
        self.link = [0] * 201
        self.atloc = [0] * (maxloc + 1)
        self.abb = [0] * (maxloc + 1)
        self.holdng = 0

        # Condition bits per location, plus forced-motion detection (COND=2).
        self.cond = [0] * (maxloc + 1)
        for loc, bits in d.cond.items():
            self.cond[loc] = bits
        for loc in d.long_desc:
            k = d.key.get(loc, 0)
            if k and _mod(abs(d.travel[k]), 1000) == 1:
                self.cond[loc] = 2

        # Object mnemonics.
        self.KEYS = self._v("KEYS", 1); self.LAMP = self._v("LAMP", 1)
        self.GRATE = self._v("GRATE", 1); self.CAGE = self._v("CAGE", 1)
        self.ROD = self._v("ROD", 1); self.ROD2 = self.ROD + 1
        self.STEPS = self._v("STEPS", 1); self.BIRD = self._v("BIRD", 1)
        self.DOOR = self._v("DOOR", 1); self.PILLOW = self._v("PILLO", 1)
        self.SNAKE = self._v("SNAKE", 1); self.FISSUR = self._v("FISSU", 1)
        self.TABLET = self._v("TABLE", 1); self.CLAM = self._v("CLAM", 1)
        self.OYSTER = self._v("OYSTE", 1); self.MAGZIN = self._v("MAGAZ", 1)
        self.DWARF = self._v("DWARF", 1); self.KNIFE = self._v("KNIFE", 1)
        self.FOOD = self._v("FOOD", 1); self.BOTTLE = self._v("BOTTL", 1)
        self.WATER = self._v("WATER", 1); self.OIL = self._v("OIL", 1)
        self.PLANT = self._v("PLANT", 1); self.PLANT2 = self.PLANT + 1
        self.AXE = self._v("AXE", 1); self.MIRROR = self._v("MIRRO", 1)
        self.DRAGON = self._v("DRAGO", 1); self.CHASM = self._v("CHASM", 1)
        self.TROLL = self._v("TROLL", 1); self.TROLL2 = self.TROLL + 1
        self.BEAR = self._v("BEAR", 1); self.MESSAG = self._v("MESSA", 1)
        self.VEND = self._v("VENDI", 1); self.BATTER = self._v("BATTE", 1)
        self.NUGGET = self._v("GOLD", 1); self.COINS = self._v("COINS", 1)
        self.CHEST = self._v("CHEST", 1); self.EGGS = self._v("EGGS", 1)
        self.TRIDNT = self._v("TRIDE", 1); self.VASE = self._v("VASE", 1)
        self.EMRALD = self._v("EMERA", 1); self.PYRAM = self._v("PYRAM", 1)
        self.PEARL = self._v("PEARL", 1); self.RUG = self._v("RUG", 1)
        self.CHAIN = self._v("CHAIN", 1)
        self.SPICES = 0  # never assigned in advent.for; PROP(SPICES) reads prop[0]

        # Motion-verb mnemonics.
        self.BACK = self._v("BACK", 0); self.LOOK = self._v("LOOK", 0)
        self.CAVE = self._v("CAVE", 0); self.NULL = self._v("NULL", 0)
        self.ENTRNC = self._v("ENTRA", 0); self.DPRSSN = self._v("DEPRE", 0)

        # Action-verb mnemonics.
        self.SAY = self._v("SAY", 2); self.LOCK = self._v("LOCK", 2)
        self.THROW = self._v("THROW", 2); self.FIND = self._v("FIND", 2)
        self.INVENT = self._v("INVEN", 2)

        # Objects/props initial layout (see advent.for labels 1101-1200).
        for k in range(100, 0, -1):
            if d.fixd.get(k, 0) > 0:
                self._drop(k + 100, d.fixd[k])
                self._drop(k, d.plac[k])
        for k in range(100, 0, -1):
            self.fixed[k] = d.fixd.get(k, 0)
            if d.plac.get(k, 0) != 0 and d.fixd.get(k, 0) <= 0:
                self._drop(k, d.plac[k])

        # Treasures start with prop -1; TALLY counts those not yet located.
        self.tally = 0
        self.tally2 = 0
        for i in range(50, self.MAXTRS + 1):
            if i in d.has_text:
                self.prop[i] = -1
            self.tally -= self.prop[i]

        # Hints.
        self.hintlc = [0] * (d.hntmax + 1)
        self.hinted = [False] * (d.hntmax + 1)

        # Dwarves (indices 1..6; 6 is the pirate).
        self.chloc = 114
        self.chloc2 = 140
        self.dseen = [False] * 7
        self.dflag = 0
        self.dloc = [0, 19, 27, 33, 44, 64, self.chloc]
        self.odloc = [0] * 7
        self.daltlc = 18

        # Misc flags/counters.
        self.turns = 0
        self.lmwarn = False
        self.iwest = 0
        self.knfloc = 0
        self.detail = 0
        self.abbnum = 5
        self.maxdie = 0
        for i in range(0, 5):
            if d.rtext.get(2 * i + 81, 0):
                self.maxdie = i + 1
        self.numdie = 0
        self.dkill = 0
        self.foobar = 0
        self.bonus = 0
        self.clock1 = 30
        self.clock2 = 50
        self.saved = -1  # -1 == did not bypass the "START" call (never mad-max dwarves)
        self.closng = False
        self.panic = False
        self.closed = False
        self.gaveup = False
        self.scorng = False
        self.wzdark = False
        self.demo = False

        self.loc = 0
        self.newloc = 1
        self.oldloc = 0
        self.oldlc2 = 0
        self.limit = 330

        # Transient parse registers (locals in the FORTRAN; instance-scoped here
        # so labels can share them the way the flat FORTRAN scope did).
        self.k = 0
        self.spk = 0
        self.verb = 0
        self.obj = 0
        self.ll = 0
        self.kk = 0
        self.hint = 0
        self.wd1 = None
        self.wd2 = None
        self.wd1_raw = None
        self.wd2_raw = None

    # -------------------------------------------------------------- predicates

    def _toting(self, obj): return self.place[obj] == -1
    def _here(self, obj): return self.place[obj] == self.loc or self._toting(obj)
    def _at(self, obj): return self.place[obj] == self.loc or self.fixed[obj] == self.loc
    def _forced(self, loc): return self.cond[loc] == 2
    def _bitset(self, loc, n): return (self.cond[loc] & (1 << n)) != 0

    def _dark(self):
        return (self.cond[self.loc] & 1) == 0 and (
            self.prop[self.LAMP] == 0 or not self._here(self.LAMP))

    def _liq2(self, pbottl):
        return (1 - pbottl) * self.WATER + _div(pbottl, 2) * (self.WATER + self.OIL)

    def _liq(self):
        pb = self.prop[self.BOTTLE]
        return self._liq2(max(pb, -1 - pb))

    def _liqloc(self, loc):
        c = self.cond[loc]
        return self._liq2((_mod(_div(c, 2) * 2, 8) - 5) * _mod(_div(c, 4), 2) + 1)

    def _pct(self, n): return self.rng.pct(n)

    # -------------------------------------------------------- object movement

    def _carry(self, obj, where):
        if obj <= 100:
            if self.place[obj] == -1:
                return
            self.place[obj] = -1
            self.holdng += 1
        if self.atloc[where] == obj:
            self.atloc[where] = self.link[obj]
            return
        temp = self.atloc[where]
        while self.link[temp] != obj:
            temp = self.link[temp]
        self.link[temp] = self.link[obj]

    def _drop(self, obj, where):
        if obj > 100:
            self.fixed[obj - 100] = where
        else:
            if self.place[obj] == -1:
                self.holdng -= 1
            self.place[obj] = where
        if where <= 0:
            return
        self.link[obj] = self.atloc[where]
        self.atloc[where] = obj

    def _move(self, obj, where):
        frm = self.place[obj] if obj <= 100 else self.fixed[obj - 100]
        if 0 < frm <= 300:
            self._carry(obj, frm)
        self._drop(obj, where)

    def _put(self, obj, where, pval):
        self._move(obj, where)
        return -1 - pval

    def _juggle(self, obj):
        i, j = self.place[obj], self.fixed[obj]
        self._move(obj, i)
        self._move(obj + 100, j)

    def _dstroy(self, obj):
        self._move(obj, 0)

    # ---------------------------------------------------------------- output

    def _emit(self, text) -> None:
        if not text or text.startswith(">$<"):
            return
        text = text.expandtabs()
        self.transcript.append(text)
        if self._write is not None:
            self._write(text)

    def _speak(self, text):
        self._emit(text)

    def _rspeak(self, i):
        if i:
            self._emit(self.data.rtext.get(i))

    def _mspeak(self, i):
        if i:
            self._emit(self.data.mtext.get(i))

    def _pspeak(self, obj, skip):
        if skip < 0:
            self._emit(self.data.inventory.get(obj))
            return
        msgs = self.data.prop_msg.get(obj)
        if msgs and skip < len(msgs):
            self._emit(msgs[skip])

    def _describe_word(self, key5, raw):
        """Echo an input word for 'I see no X' style messages.

        The FORTRAN's parser upper-cases input, so echoed words are upper-case
        while the surrounding hardcoded text keeps its original mixed case.
        """
        return (raw or key5 or "").upper()

    # ----------------------------------------------------------------- input

    def _get_command(self):
        """Read a line and split into up to two words (mirrors ``GETIN``)."""
        while True:
            line = self._read_line()
            if line is None:
                raise EOFError
            toks = line.split()
            if not toks:
                continue
            self.wd1_raw = toks[0]
            self.wd1 = toks[0][:5].upper()
            if len(toks) > 1:
                self.wd2_raw = toks[1]
                self.wd2 = toks[1][:5].upper()
            else:
                self.wd2_raw = None
                self.wd2 = None
            return

    def _yes(self, x, y, z) -> bool:
        """Print message x, read yes/no; print y on yes / z on no (``YESX``)."""
        while True:
            if x:
                self._rspeak(x)
            self._get_command()
            reply = self.wd1
            if reply in ("YES", "Y"):
                if y:
                    self._rspeak(y)
                return True
            if reply in ("NO", "N"):
                if z:
                    self._rspeak(z)
                return False
            self._emit("Please answer the question.")

    # ------------------------------------------------------------- dispatch

    def _build_dispatch(self):
        names = [
            "2", "2000", "2600", "2608", "19999", "3000", "4000", "4080",
            "4090", "5000", "5010", "5100", "8", "9", "11", "12", "13", "14",
            "16", "20", "30", "40", "50", "30000", "30300", "2009", "2010",
            "2011", "2012", "2800", "90", "99", "95",
            "10000", "11000", "12000", "12200", "12400", "12600", "13000",
            "19000", "20000",
            "8000", "8010", "8040", "8140", "8180", "8200", "8240", "8241",
            "8250", "8260", "8270", "8300", "8310",
            "9010", "9020", "9021", "9024", "9025", "9026", "9027",
            "9030", "9040", "9046", "9048", "9049", "9070", "9080", "9090",
            "9120", "9130", "9132", "9140", "9150", "9160", "9170",
            "9172", "9176", "9177", "9178", "9190", "9210", "9212", "9213",
            "9214", "9215", "9220", "9222", "9230", "9270", "9280",
            "9290",
        ]
        self._labels = {n: getattr(self, "_l" + n) for n in names}

    def _drive(self, start="2"):
        label = start
        while label is not None:
            label = self._labels[label]()

    # -------------------------------------------------------------- run / API

    def start(self):
        """Emit the welcome banner and ask for instructions (FORTRAN label 1)."""
        self.hinted[3] = self._yes(65, 1, 0)
        self.newloc = 1
        self.limit = 1000 if self.hinted[3] else 330

    def run(self, read_line, write=None):
        """Drive the game to completion using ``read_line``/``write`` callbacks."""
        self._read_line = read_line
        self._write = write
        try:
            self.start()
            self._drive()
        except (_GameOver, EOFError):
            pass

    def resume(self, read_line, write=None):
        """Continue a restored game: re-describe the room, then take commands.

        Starts at label 2000 (describe location) rather than the top of the
        turn loop, so the dwarves don't advance merely because the game was
        reloaded -- that happens on the next actual move, as normal.
        """
        self._read_line = read_line
        self._write = write
        self.wzdark = False  # don't risk a spurious dark-pit death on reload
        try:
            self._drive(start="2000")
        except (_GameOver, EOFError):
            pass

    # ---- save / restore ----------------------------------------------------

    _NOSAVE = frozenset({"data", "rng", "_labels", "_read_line", "_write"})

    def save_state(self) -> dict:
        """A JSON-serialisable snapshot of the whole game (valid at a prompt)."""
        attrs = {k: v for k, v in self.__dict__.items() if k not in self._NOSAVE}
        return {"version": 1, "attrs": attrs, "rng": self.rng.get_state()}

    def load_state(self, blob: dict) -> None:
        """Restore a snapshot produced by :meth:`save_state`."""
        for key, value in blob["attrs"].items():
            setattr(self, key, value)
        self.rng.set_state(blob["rng"])

    def play_commands(self, commands) -> str:
        """Feed a list of command strings; return the full transcript."""
        it = iter(commands)

        def rl():
            try:
                return next(it)
            except StopIteration:
                raise EOFError

        out: list[str] = []
        self.run(rl, out.append)
        return "\n".join(out)

    # ======================================================== the game labels
    # Each method mirrors the identically-numbered FORTRAN statement label and
    # returns the name of the next label (or None to end the game).

    def _l2(self):
        # Closing check: can't leave the cave once it's closing.
        if not (self.newloc >= 9 or self.newloc == 0 or not self.closng):
            self._rspeak(130)
            self.newloc = self.loc
            if not self.panic:
                self.clock2 = 15
            self.panic = True
        # 71: a dwarf who has seen us and came from where we're going blocks us.
        if not (self.newloc == self.loc or self._forced(self.loc)
                or self._bitset(self.loc, 3)):
            for i in range(1, 6):
                if self.odloc[i] == self.newloc and self.dseen[i]:
                    self.newloc = self.loc
                    self._rspeak(2)
                    break
        self.loc = self.newloc  # 74
        return self._dwarves()

    def _dwarves(self):
        # advent.for labels 74..6030.  Returns "2000" (describe) or "99" (dead).
        if not (self.loc == 0 or self._forced(self.loc)
                or self._bitset(self.newloc, 3)):
            if self.dflag == 0:
                if self.loc >= 15:
                    self.dflag = 1
            else:
                res = self._dwarves_active()
                if res is not None:
                    return res
        return "2000"

    def _dwarves_active(self):
        # 6000: first encounter kills 0..2 of the 5 dwarves.
        if self.dflag == 1:
            if self.loc < 15 or self._pct(95):
                return None
            self.dflag = 2
            for _ in range(2):
                j = 1 + self.rng.ran(5)
                if self._pct(50) and self.saved == -1:
                    self.dloc[j] = 0
            for i in range(1, 6):
                if self.dloc[i] == self.loc:
                    self.dloc[i] = self.daltlc
                self.odloc[i] = self.dloc[i]
            self._rspeak(3)
            self._drop(self.AXE, self.loc)
            return None

        # 6010: move each dwarf; a following dwarf sticks with us and may attack.
        dtotal = attack = stick = 0
        tk = [0] * 21
        for i in range(1, 7):
            if self.dloc[i] == 0:
                continue
            j = 1
            kk = self.data.key.get(self.dloc[i], 0)
            if kk != 0:
                while True:  # 6012
                    newloc = _mod(_div(abs(self.data.travel[kk]), 1000), 1000)
                    if not (newloc > 300 or newloc < 15 or newloc == self.odloc[i]
                            or (j > 1 and newloc == tk[j - 1]) or j >= 20
                            or newloc == self.dloc[i] or self._forced(newloc)
                            or (i == 6 and self._bitset(newloc, 3))
                            or _div(abs(self.data.travel[kk]), 1000000) == 100):
                        tk[j] = newloc
                        j += 1
                    kk += 1  # 6014
                    if self.data.travel[kk - 1] >= 0:
                        continue
                    break
            tk[j] = self.odloc[i]  # 6016
            if j >= 2:
                j -= 1
            j = 1 + self.rng.ran(j)
            self.odloc[i] = self.dloc[i]
            self.dloc[i] = tk[j]
            self.dseen[i] = (self.dseen[i] and self.loc >= 15) or (
                self.dloc[i] == self.loc or self.odloc[i] == self.loc)
            if not self.dseen[i]:
                continue
            self.dloc[i] = self.loc
            if i == 6:
                res = self._pirate()
                if res == "continue":
                    continue
            else:
                # 6027: a threatening dwarf is in the room.
                dtotal += 1
                if self.odloc[i] == self.dloc[i]:
                    attack += 1
                    if self.knfloc >= 0:
                        self.knfloc = self.loc
                    if self.rng.ran(1000) < 95 * (self.dflag - 2):
                        stick += 1
        return self._dwarf_report(dtotal, attack, stick)

    def _pirate(self):
        # 6027-path for the sixth dwarf (the pirate).  Returns "continue".
        if self.loc == self.chloc or self.prop[self.CHEST] >= 0:
            return "continue"
        k = 0
        stolen = False
        for j in range(50, self.MAXTRS + 1):
            if j == self.PYRAM and (self.loc == self.data.plac[self.PYRAM]
                                    or self.loc == self.data.plac[self.EMRALD]):
                continue
            if self._toting(j):
                stolen = True
                break
            if self._here(j):
                k = 1
        if not stolen:
            if (self.tally == self.tally2 + 1 and k == 0
                    and self.place[self.CHEST] == 0 and self._here(self.LAMP)
                    and self.prop[self.LAMP] == 1):
                # 6025: pirate leaves a message to the chest.
                self._rspeak(186)
                self._move(self.CHEST, self.chloc)
                self._move(self.MESSAG, self.chloc2)
                self.dloc[6] = self.chloc
                self.odloc[6] = self.chloc
                self.dseen[6] = False
                return "continue"
            if self.odloc[6] != self.dloc[6] and self._pct(20):
                self._rspeak(127)
            return "continue"
        # 6022: he robs us.
        self._rspeak(128)
        if self.place[self.MESSAG] == 0:
            self._move(self.CHEST, self.chloc)
        self._move(self.MESSAG, self.chloc2)
        for j in range(50, self.MAXTRS + 1):
            if j == self.PYRAM and (self.loc == self.data.plac[self.PYRAM]
                                    or self.loc == self.data.plac[self.EMRALD]):
                continue
            if self._at(j) and self.fixed[j] == 0:
                self._carry(j, self.loc)
            if self._toting(j):
                self._drop(j, self.chloc)
        self.dloc[6] = self.chloc
        self.odloc[6] = self.chloc
        self.dseen[6] = False
        return "continue"

    def _dwarf_report(self, dtotal, attack, stick):
        if dtotal == 0:
            return "2000"
        if dtotal == 1:
            self._rspeak(4)
        else:
            self._emit("There are {} threatening little dwarves in the room "
                       "with you.".format(dtotal))
        if attack == 0:
            return "2000"
        if self.dflag == 2:
            self.dflag = 3
        if self.saved != -1:
            self.dflag = 20
        if attack == 1:
            self._rspeak(5)
            k = 52
        else:
            self._emit("{} of them throw knives at you!".format(attack))
            k = 6
        if stick <= 1:  # 82
            self._rspeak(k + stick)
            if stick == 0:
                return "2000"
        else:
            self._emit("{} of them get you!".format(stick))
        self.oldlc2 = self.loc  # 84
        return "99"

    def _l2000(self):
        if self.loc == 0:
            return "99"
        short = self.data.short_desc.get(self.loc)
        use_long = (self.abb[self.loc] % self.abbnum == 0) or (short is None)
        text = self.data.long_desc.get(self.loc) if use_long else short
        if not (self._forced(self.loc) or not self._dark()):
            if self.wzdark and self._pct(35):
                return "90"
            text = self.data.rtext.get(16)
        if self._toting(self.BEAR):
            self._rspeak(141)
        self._speak(text)
        self.k = 1
        if self._forced(self.loc):
            return "8"
        if self.loc == 33 and self._pct(25) and not self.closng:
            self._rspeak(8)
        if self._dark():
            return "2012"
        self.abb[self.loc] += 1
        i = self.atloc[self.loc]
        while i != 0:  # 2004
            obj = i if i <= 100 else i - 100
            skip = False
            if obj == self.STEPS and self._toting(self.NUGGET):
                skip = True
            elif self.prop[obj] < 0:
                if self.closed:
                    skip = True
                else:
                    self.prop[obj] = 0
                    if obj == self.RUG or obj == self.CHAIN:
                        self.prop[obj] = 1
                    self.tally -= 1
                    if self.tally == self.tally2 and self.tally != 0:
                        self.limit = min(35, self.limit)
            if not skip:
                kk = self.prop[obj]
                if obj == self.STEPS and self.loc == self.fixed[self.STEPS]:
                    kk = 1
                self._pspeak(obj, kk)
            i = self.link[i]
        return "2012"

    def _l2600(self):
        # Hints, closing prop fix-up, then read the next command.
        self._check_hints()
        if self.closed:
            if self.prop[self.OYSTER] < 0 and self._toting(self.OYSTER):
                self._pspeak(self.OYSTER, 1)
            for i in range(1, 101):
                if self._toting(i) and self.prop[i] < 0:
                    self.prop[i] = -1 - self.prop[i]
        self.wzdark = self._dark()
        if self.knfloc > 0 and self.knfloc != self.loc:
            self.knfloc = 0
        self.rng.ran(1)
        self._get_command()
        return "2608"

    def _check_hints(self):
        for hint in range(4, self.data.hntmax + 1):
            if self.hinted[hint]:
                continue
            if not self._bitset(self.loc, hint):
                self.hintlc[hint] = -1
            self.hintlc[hint] += 1
            if self.hintlc[hint] >= self.data.hints[hint][0]:
                self._offer_hint(hint)

    def _offer_hint(self, hint):
        turns, points, qmsg, hmsg = self.data.hints[hint]
        conds = {
            4: lambda: self.prop[self.GRATE] == 0 and not self._here(self.KEYS),
            5: lambda: (self._here(self.BIRD) and self._toting(self.ROD)
                        and self.obj == self.BIRD),
            6: lambda: self._here(self.SNAKE) and not self._here(self.BIRD),
            7: lambda: (self.atloc[self.loc] == 0 and self.atloc[self.oldloc] == 0
                        and self.atloc[self.oldlc2] == 0 and self.holdng > 1),
            8: lambda: self.prop[self.EMRALD] != -1 and self.prop[self.PYRAM] == -1,
            9: lambda: True,
        }
        met = conds[hint]()
        if not met:
            if hint != 5:  # bird hint (40500) leaves hintlc; others reset it
                self.hintlc[hint] = 0
            return
        self.hintlc[hint] = 0
        if not self._yes(qmsg, 0, 54):
            return
        self._emit("I am prepared to give you a hint, but it will cost you"
                   "{:2d} points.".format(points))
        self.hinted[hint] = self._yes(175, hmsg, 54)
        if self.hinted[hint] and self.limit > 30:
            self.limit += 30 * points

    def _l2608(self):
        self.foobar = min(0, -self.foobar)
        self.turns += 1
        if self.verb == self.SAY and self.wd2 is not None:
            self.verb = 0
        if self.verb == self.SAY:
            return "4090"
        if self.tally == 0 and self.loc >= 15 and self.loc != 33:
            self.clock1 -= 1
        if self.clock1 == 0:
            return "10000"
        if self.clock1 < 0:
            self.clock2 -= 1
        if self.clock2 == 0:
            return "11000"
        if self.prop[self.LAMP] == 1:
            self.limit -= 1
        if (self.limit <= 30 and self._here(self.BATTER)
                and self.prop[self.BATTER] == 0 and self._here(self.LAMP)):
            return "12000"
        if self.limit == 0:
            return "12400"
        if self.limit < 0 and self.loc <= 8:
            return "12600"
        if self.limit <= 30:
            return "12200"
        return "19999"

    def _l19999(self):
        self.k = 43
        if self._liqloc(self.loc) == self.WATER:
            self.k = 70
        if self.wd1 == "ENTER" and self.wd2 in ("STREA", "WATER"):
            return "2010"
        if self.wd1 == "ENTER" and self.wd2 is not None:
            return "2800"
        if not ((self.wd1 != "WATER" and self.wd1 != "OIL")
                or (self.wd2 != "PLANT" and self.wd2 != "DOOR")):
            if self._at(self._v(self.wd2, 1)):
                self.wd2 = "POUR"
                self.wd2_raw = "pour"
        # 2610
        if self.wd1 == "WEST":
            self.iwest += 1
            if self.iwest == 10:
                self._rspeak(17)
        # 2630
        i = self._v(self.wd1, -1)
        if i == -1:
            return "3000"
        self.k = _mod(i, 1000)
        kq = _div(i, 1000)
        return {0: "8", 1: "5000", 2: "4000", 3: "2010"}[kq]

    def _l2800(self):
        self.wd1 = self.wd2
        self.wd1_raw = self.wd2_raw
        self.wd2 = None
        self.wd2_raw = None
        return "19999"  # FORTRAN goes to 2610; the WEST/vocab work re-runs harmlessly

    def _l3000(self):
        self.spk = 60
        if self._pct(20):
            self.spk = 61
        if self._pct(20):
            self.spk = 13
        self._rspeak(self.spk)
        return "2600"

    def _l2009(self):
        self.k = 54
        return "2010"

    def _l2010(self):
        self.spk = self.k
        return "2011"

    def _l2011(self):
        self._rspeak(self.spk)
        return "2012"

    def _l2012(self):
        self.verb = 0
        self.obj = 0
        return "2600"

    # ---- verb dispatch -----------------------------------------------------

    _INTRANSITIVE = [
        None, "8010", "8000", "8000", "8040", "2009", "8040", "9070", "9080",
        "8000", "8000", "2011", "9120", "9130", "8140", "9150", "8000", "8000",
        "8180", "8000", "8200", "8000", "9220", "9230", "8240", "8250", "8260",
        "8270", "8000", "8000", "8300", "8310",
    ]
    _TRANSITIVE = [
        None, "9010", "9020", "9030", "9040", "2009", "9040", "9070", "9080",
        "9090", "2011", "2011", "9120", "9130", "9140", "9150", "9160", "9170",
        "2011", "9190", "9190", "9210", "9220", "9230", "2011", "2011", "2011",
        "9270", "9280", "9290", "2011", "2011",
    ]

    def _l4000(self):
        self.verb = self.k
        self.spk = self.data.actspk.get(self.verb, 0)
        if self.wd2 is not None and self.verb != self.SAY:
            return "2800"
        if self.verb == self.SAY:
            self.obj = self.wd2  # note: a word key, not an object number
        if self.obj != 0 and self.obj is not None:
            return "4090"
        return "4080"

    def _l4080(self):
        return self._INTRANSITIVE[self.verb]

    def _l4090(self):
        return self._TRANSITIVE[self.verb]

    def _l5000(self):
        self.obj = self.k
        if self.fixed[self.k] != self.loc and not self._here(self.k):
            return "5100"
        return "5010"

    def _l5010(self):
        if self.wd2 is not None:
            return "2800"
        if self.verb != 0:
            return "4090"
        word = self._describe_word(self.wd1, self.wd1_raw)
        self._emit("What do you want to do with the {}?".format(word))
        return "2600"

    def _l5100(self):
        k = self.k
        if k == self.GRATE:
            if self.loc in (1, 4, 7):
                k = self.DPRSSN
            if 9 < self.loc < 15:
                k = self.ENTRNC
            if k != self.GRATE:
                self.k = k
                return "8"
        if k == self.DWARF:
            for i in range(1, 6):
                if self.dloc[i] == self.loc and self.dflag >= 2:
                    return "5010"
        if (self._liq() == k and self._here(self.BOTTLE)) or k == self._liqloc(self.loc):
            return "5010"
        if not (self.obj != self.PLANT or not self._at(self.PLANT2)
                or self.prop[self.PLANT2] == 0):
            self.obj = self.PLANT2
            return "5010"
        if self.obj == self.KNIFE and self.knfloc == self.loc:
            self.knfloc = -1
            self.spk = 116
            return "2011"
        if self.obj == self.ROD and self._here(self.ROD2):
            self.obj = self.ROD2
            return "5010"
        if (self.verb == self.FIND or self.verb == self.INVENT) and self.wd2 is None:
            return "5010"
        word = self._describe_word(self.wd1, self.wd1_raw)
        self._emit("I see no {} here.".format(word))
        return "2012"

    # ---- motion resolution -------------------------------------------------

    def _l8(self):
        self.kk = self.data.key.get(self.loc, 0)
        self.newloc = self.loc
        if self.k == self.NULL:
            return "2"
        if self.k == self.BACK:
            return "20"
        if self.k == self.LOOK:
            return "30"
        if self.k == self.CAVE:
            return "40"
        self.oldlc2 = self.oldloc
        self.oldloc = self.loc
        return "9"

    def _l9(self):
        self.ll = abs(self.data.travel[self.kk])
        if _mod(self.ll, 1000) == 1 or _mod(self.ll, 1000) == self.k:
            self.ll = _div(self.ll, 1000)  # label 10
            return "11"
        if self.data.travel[self.kk] < 0:
            return "50"
        self.kk += 1
        return "9"

    def _l11(self):
        self.newloc = _div(self.ll, 1000)
        self.k = _mod(self.newloc, 100)
        if self.newloc <= 300:
            return "13"
        if self.prop[self.k] != _div(self.newloc, 100) - 3:
            return "16"
        return "12"

    def _l12(self):
        while True:
            if self.data.travel[self.kk] < 0:
                raise _GameOver("bug 25: conditional travel with no alternative")
            self.kk += 1
            self.newloc = _div(abs(self.data.travel[self.kk]), 1000)
            if self.newloc != self.ll:
                break
        self.ll = self.newloc
        return "11"

    def _l13(self):
        if self.newloc <= 100:
            return "14"
        if self._toting(self.k) or (self.newloc > 200 and self._at(self.k)):
            return "16"
        return "12"

    def _l14(self):
        if self.newloc != 0 and not self._pct(self.newloc):
            return "12"
        return "16"

    def _l16(self):
        self.newloc = _mod(self.ll, 1000)
        if self.newloc <= 300:
            return "2"
        if self.newloc <= 500:
            return "30000"
        self._rspeak(self.newloc - 500)
        self.newloc = self.loc
        return "2"

    def _l20(self):
        k = self.oldloc
        if self._forced(k):
            k = self.oldlc2
        self.oldlc2 = self.oldloc
        self.oldloc = self.loc
        k2 = 0
        if k == self.loc:
            self._rspeak(91)
            return "2"
        kk = self.kk
        while True:  # 21
            ll = _mod(_div(abs(self.data.travel[kk]), 1000), 1000)
            if ll == k:
                break
            if ll <= 300:
                j = self.data.key.get(ll, 0)
                if self._forced(ll) and _mod(_div(abs(self.data.travel[j]), 1000), 1000) == k:
                    k2 = kk
            if self.data.travel[kk] < 0:  # 22 -> 23
                kk = k2
                if kk == 0:
                    self._rspeak(140)
                    return "2"
                break
            kk += 1
        # 25
        self.k = _mod(abs(self.data.travel[kk]), 1000)
        self.kk = self.data.key.get(self.loc, 0)
        return "9"

    def _l30(self):
        if self.detail < 3:
            self._rspeak(15)
        self.detail += 1
        self.wzdark = False
        self.abb[self.loc] = 0
        return "2"

    def _l40(self):
        self._rspeak(57 if self.loc < 8 else 58)
        return "2"

    def _l50(self):
        k = self.k
        spk = 12
        if 43 <= k <= 50:
            spk = 9
        if k in (29, 30):
            spk = 9
        if k in (7, 36, 37):
            spk = 10
        if k in (11, 19):
            spk = 11
        if self.verb in (self.FIND, self.INVENT):
            spk = 59
        if k in (62, 65):
            spk = 42
        if k == 17:
            spk = 80
        self._rspeak(spk)
        return "2"

    # ---- special travel ----------------------------------------------------

    def _l30000(self):
        n = self.newloc - 300
        if n == 1:
            # 30100 Plover alcove: may carry only the emerald through.
            self.newloc = 99 + 100 - self.loc
            if self.holdng == 0 or (self.holdng == 1 and self._toting(self.EMRALD)):
                return "2"
            self.newloc = self.loc
            self._rspeak(117)
            return "2"
        if n == 2:
            # 30200 Plover transport: drop the emerald, then re-enter decode.
            self._drop(self.EMRALD, self.loc)
            return "12"
        return "30300"

    def _l30300(self):
        if self.prop[self.TROLL] != 1:
            # 30310
            self.newloc = self.data.plac[self.TROLL] + self.data.fixd[self.TROLL] - self.loc
            if self.prop[self.TROLL] == 0:
                self.prop[self.TROLL] = 1
            if not self._toting(self.BEAR):
                return "2"
            self._rspeak(162)
            self.prop[self.CHASM] = 1
            self.prop[self.TROLL] = 2
            self._drop(self.BEAR, self.newloc)
            self.fixed[self.BEAR] = -1
            self.prop[self.BEAR] = 3
            if self.prop[self.SPICES] < 0:
                self.tally2 += 1
            self.oldlc2 = self.newloc
            return "99"
        self._pspeak(self.TROLL, 1)
        self.prop[self.TROLL] = 0
        self._move(self.TROLL2, 0)
        self._move(self.TROLL2 + 100, 0)
        self._move(self.TROLL, self.data.plac[self.TROLL])
        self._move(self.TROLL + 100, self.data.fixd[self.TROLL])
        self._juggle(self.CHASM)
        self.newloc = self.loc
        return "2"

    # ---- death / reincarnation --------------------------------------------

    def _l90(self):
        self._rspeak(23)
        self.oldlc2 = self.loc
        return "99"

    def _l99(self):
        if self.closng:
            return "95"
        yea = self._yes(81 + self.numdie * 2, 82 + self.numdie * 2, 54)
        self.numdie += 1
        if self.numdie == self.maxdie or not yea:
            return "20000"
        self.place[self.WATER] = 0
        self.place[self.OIL] = 0
        if self._toting(self.LAMP):
            self.prop[self.LAMP] = 0
        for j in range(1, 101):
            i = 101 - j
            if not self._toting(i):
                continue
            k = self.oldlc2
            if i == self.LAMP:
                k = 1
            self._drop(i, k)
        self.loc = 3
        self.oldloc = self.loc
        return "2000"

    def _l95(self):
        self._rspeak(131)
        self.numdie += 1
        return "20000"

    # ---- action verbs ------------------------------------------------------

    def _l8000(self):
        word = self._describe_word(self.wd1, self.wd1_raw)
        self._emit("{} What?".format(word))
        self.obj = 0
        return "2600"

    def _l8010(self):
        if self.atloc[self.loc] == 0 or self.link[self.atloc[self.loc]] != 0:
            return "8000"
        for i in range(1, 6):
            if self.dloc[i] == self.loc and self.dflag >= 2:
                return "8000"
        self.obj = self.atloc[self.loc]
        return "9010"

    def _l8040(self):  # lock / unlock, no object given
        self.spk = 28
        if self._here(self.CLAM):
            self.obj = self.CLAM
        if self._here(self.OYSTER):
            self.obj = self.OYSTER
        if self._at(self.DOOR):
            self.obj = self.DOOR
        if self._at(self.GRATE):
            self.obj = self.GRATE
        if self.obj != 0 and self._here(self.CHAIN):
            return "8000"
        if self._here(self.CHAIN):
            self.obj = self.CHAIN
        if self.obj == 0:
            return "2011"
        return "9040"

    def _l9010(self):
        if self._toting(self.obj):
            return "2011"
        self.spk = 25
        if self.obj == self.PLANT and self.prop[self.PLANT] <= 0:
            self.spk = 115
        if self.obj == self.BEAR and self.prop[self.BEAR] == 1:
            self.spk = 169
        if self.obj == self.CHAIN and self.prop[self.BEAR] != 0:
            self.spk = 170
        if self.fixed[self.obj] != 0:
            return "2011"
        if self.obj == self.WATER or self.obj == self.OIL:
            if self._here(self.BOTTLE) and self._liq() == self.obj:
                self.obj = self.BOTTLE  # 9018
            else:
                self.obj = self.BOTTLE
                if self._toting(self.BOTTLE) and self.prop[self.BOTTLE] == 1:
                    return "9220"
                if self.prop[self.BOTTLE] != 1:
                    self.spk = 105
                if not self._toting(self.BOTTLE):
                    self.spk = 104
                return "2011"
        # 9017
        if self.holdng >= 7:
            self._rspeak(92)
            return "2012"
        if self.obj == self.BIRD and self.prop[self.BIRD] == 0:
            if self._toting(self.ROD):
                self._rspeak(26)
                return "2012"
            if not self._toting(self.CAGE):
                self._rspeak(27)
                return "2012"
            self.prop[self.BIRD] = 1  # 9015
        if self.obj in (self.BIRD, self.CAGE) and self.prop[self.BIRD] != 0:
            self._carry(self.BIRD + self.CAGE - self.obj, self.loc)
        self._carry(self.obj, self.loc)
        k = self._liq()
        if self.obj == self.BOTTLE and k != 0:
            self.place[k] = -1
        return "2009"

    def _l9020(self):
        if (self._toting(self.ROD2) and self.obj == self.ROD
                and not self._toting(self.ROD)):
            self.obj = self.ROD2
        if not self._toting(self.obj):
            return "2011"
        if self.obj == self.BIRD and self._here(self.SNAKE):
            self._rspeak(30)
            if self.closed:
                return "19000"
            self._dstroy(self.SNAKE)
            self.prop[self.SNAKE] = 1
            return "9021"
        return "9024"

    def _l9021(self):
        k = self._liq()
        if k == self.obj:
            self.obj = self.BOTTLE
        if self.obj == self.BOTTLE and k != 0:
            self.place[k] = 0
        if self.obj == self.CAGE and self.prop[self.BIRD] != 0:
            self._drop(self.BIRD, self.loc)
        if self.obj == self.BIRD:
            self.prop[self.BIRD] = 0
        self._drop(self.obj, self.loc)
        return "2012"

    def _l9024(self):
        if self.obj == self.COINS and self._here(self.VEND):
            self._dstroy(self.COINS)
            self._drop(self.BATTER, self.loc)
            self._pspeak(self.BATTER, 0)
            return "2012"
        return "9025"

    def _l9025(self):
        if (self.obj == self.BIRD and self._at(self.DRAGON)
                and self.prop[self.DRAGON] == 0):
            self._rspeak(154)
            self._dstroy(self.BIRD)
            self.prop[self.BIRD] = 0
            if self.place[self.SNAKE] == self.data.plac[self.SNAKE]:
                self.tally2 += 1
            return "2012"
        return "9026"

    def _l9026(self):
        if self.obj == self.BEAR and self._at(self.TROLL):
            self._rspeak(163)
            self._move(self.TROLL, 0)
            self._move(self.TROLL + 100, 0)
            self._move(self.TROLL2, self.data.plac[self.TROLL])
            self._move(self.TROLL2 + 100, self.data.fixd[self.TROLL])
            self._juggle(self.CHASM)
            self.prop[self.TROLL] = 2
            return "9021"
        return "9027"

    def _l9027(self):
        if self.obj == self.VASE and self.loc != self.data.plac[self.PILLOW]:
            self.prop[self.VASE] = 2  # 9028
            if self._at(self.PILLOW):
                self.prop[self.VASE] = 0
            self._pspeak(self.VASE, self.prop[self.VASE] + 1)
            if self.prop[self.VASE] != 0:
                self.fixed[self.VASE] = -1
            return "9021"
        self._rspeak(54)
        return "9021"

    def _l9030(self):  # SAY
        raw = self.wd2_raw if self.wd2 is not None else self.wd1_raw
        say_word = self.wd2 if self.wd2 is not None else self.wd1
        if self.wd2 is not None:
            self.wd1 = self.wd2
            self.wd1_raw = self.wd2_raw
        i = self._v(self.wd1, -1)
        if i in (62, 65, 71, 2025):
            self.wd2 = None
            self.wd2_raw = None
            self.obj = 0
            return "19999"  # FORTRAN 2630; treat as a motion/magic word
        self._emit('Okay, "{}".'.format((raw or say_word or "").upper()))
        return "2012"

    def _l9040(self):  # LOCK / UNLOCK
        obj = self.obj
        if obj == self.CLAM or obj == self.OYSTER:
            return "9046"
        if obj == self.DOOR:
            self.spk = 111
        if obj == self.DOOR and self.prop[self.DOOR] == 1:
            self.spk = 54
        if obj == self.CAGE:
            self.spk = 32
        if obj == self.KEYS:
            self.spk = 55
        if obj == self.GRATE or obj == self.CHAIN:
            self.spk = 31
        if self.spk != 31 or not self._here(self.KEYS):
            return "2011"
        if obj == self.CHAIN:
            return "9048"
        if self.closng:
            self.k = 130
            if not self.panic:
                self.clock2 = 15
            self.panic = True
            return "2010"
        # 9043
        self.k = 34 + self.prop[self.GRATE]
        self.prop[self.GRATE] = 1
        if self.verb == self.LOCK:
            self.prop[self.GRATE] = 0
        self.k = self.k + 2 * self.prop[self.GRATE]
        return "2010"

    def _l9046(self):
        k = 0
        if self.obj == self.OYSTER:
            k = 1
        self.spk = 124 + k
        if self._toting(self.obj):
            self.spk = 120 + k
        if not self._toting(self.TRIDNT):
            self.spk = 122 + k
        if self.verb == self.LOCK:
            self.spk = 61
        if self.spk != 124:
            return "2011"
        self._dstroy(self.CLAM)
        self._drop(self.OYSTER, self.loc)
        self._drop(self.PEARL, 105)
        return "2011"

    def _l9048(self):
        if self.verb == self.LOCK:
            return "9049"
        self.spk = 171
        if self.prop[self.BEAR] == 0:
            self.spk = 41
        if self.prop[self.CHAIN] == 0:
            self.spk = 37
        if self.spk != 171:
            return "2011"
        self.prop[self.CHAIN] = 0
        self.fixed[self.CHAIN] = 0
        if self.prop[self.BEAR] != 3:
            self.prop[self.BEAR] = 2
        self.fixed[self.BEAR] = 2 - self.prop[self.BEAR]
        return "2011"

    def _l9049(self):
        self.spk = 172
        if self.prop[self.CHAIN] != 0:
            self.spk = 34
        if self.loc != self.data.plac[self.CHAIN]:
            self.spk = 173
        if self.spk != 172:
            return "2011"
        self.prop[self.CHAIN] = 2
        if self._toting(self.CHAIN):
            self._drop(self.CHAIN, self.loc)
        self.fixed[self.CHAIN] = -1
        return "2011"

    def _l9070(self):  # lamp on
        if not self._here(self.LAMP):
            return "2011"
        self.spk = 184
        if self.limit < 0:
            return "2011"
        self.prop[self.LAMP] = 1
        self._rspeak(39)
        if self.wzdark:
            return "2000"
        return "2012"

    def _l9080(self):  # lamp off
        if not self._here(self.LAMP):
            return "2011"
        self.prop[self.LAMP] = 0
        self._rspeak(40)
        if self._dark():
            self._rspeak(16)
        return "2012"

    def _l9090(self):  # wave
        if (not self._toting(self.obj)) and (
                self.obj != self.ROD or not self._toting(self.ROD2)):
            self.spk = 29
        if (self.obj != self.ROD or not self._at(self.FISSUR)
                or not self._toting(self.obj) or self.closng):
            return "2011"
        self.prop[self.FISSUR] = 1 - self.prop[self.FISSUR]
        self._pspeak(self.FISSUR, 2 - self.prop[self.FISSUR])
        return "2012"

    def _l9120(self):  # attack
        i = 0
        for idx in range(1, 6):
            if self.dloc[idx] == self.loc and self.dflag >= 2:
                i = idx
                break
        if self.obj == 0:
            if i != 0:
                self.obj = self.DWARF
            if self._here(self.SNAKE):
                self.obj = self.obj * 100 + self.SNAKE
            if self._at(self.DRAGON) and self.prop[self.DRAGON] == 0:
                self.obj = self.obj * 100 + self.DRAGON
            if self._at(self.TROLL):
                self.obj = self.obj * 100 + self.TROLL
            if self._here(self.BEAR) and self.prop[self.BEAR] == 0:
                self.obj = self.obj * 100 + self.BEAR
            if self.obj > 100:
                return "8000"
            if self.obj == 0:
                if self._here(self.BIRD) and self.verb != self.THROW:
                    self.obj = self.BIRD
                if self._here(self.CLAM) or self._here(self.OYSTER):
                    self.obj = 100 * self.obj + self.CLAM
                if self.obj > 100:
                    return "8000"
        # 9124
        if self.obj == self.BIRD:
            self.spk = 137
            if self.closed:
                return "2011"
            self._dstroy(self.BIRD)
            self.prop[self.BIRD] = 0
            if self.place[self.SNAKE] == self.data.plac[self.SNAKE]:
                self.tally2 += 1
            self.spk = 45
        # 9125
        if self.obj == 0:
            self.spk = 44
        if self.obj == self.CLAM or self.obj == self.OYSTER:
            self.spk = 150
        if self.obj == self.SNAKE:
            self.spk = 46
        if self.obj == self.DWARF:
            self.spk = 49
        if self.obj == self.DWARF and self.closed:
            return "19000"
        if self.obj == self.DRAGON:
            self.spk = 167
        if self.obj == self.TROLL:
            self.spk = 157
        if self.obj == self.BEAR:
            self.spk = 165 + (self.prop[self.BEAR] + 1) // 2
        if self.obj != self.DRAGON or self.prop[self.DRAGON] != 0:
            return "2011"
        # Dragon: ask, and if he insists on bare hands, he wins.
        self._rspeak(49)
        self.verb = 0
        self.obj = 0
        self._get_command()
        if self.wd1 not in ("Y", "YES"):
            return "2608"
        self._pspeak(self.DRAGON, 1)
        self.prop[self.DRAGON] = 2
        self.prop[self.RUG] = 0
        k = (self.data.plac[self.DRAGON] + self.data.fixd[self.DRAGON]) // 2
        self._move(self.DRAGON + 100, -1)
        self._move(self.RUG + 100, 0)
        self._move(self.DRAGON, k)
        self._move(self.RUG, k)
        for obj in range(1, 101):
            if (self.place[obj] == self.data.plac[self.DRAGON]
                    or self.place[obj] == self.data.fixd[self.DRAGON]):
                self._move(obj, k)
        self.loc = k
        self.k = self.NULL
        return "8"

    def _l9130(self):  # pour
        if self.obj == self.BOTTLE or self.obj == 0:
            self.obj = self._liq()
        if self.obj == 0:
            return "8000"
        if not self._toting(self.obj):
            return "2011"
        self.spk = 78
        if self.obj != self.OIL and self.obj != self.WATER:
            return "2011"
        self.prop[self.BOTTLE] = 1
        self.place[self.obj] = 0
        self.spk = 77
        if not (self._at(self.PLANT) or self._at(self.DOOR)):
            return "2011"
        if self._at(self.DOOR):
            return "9132"
        self.spk = 112
        if self.obj != self.WATER:
            return "2011"
        self._pspeak(self.PLANT, self.prop[self.PLANT] + 1)
        self.prop[self.PLANT] = _mod(self.prop[self.PLANT] + 2, 6)
        self.prop[self.PLANT2] = _div(self.prop[self.PLANT], 2)
        self.k = self.NULL
        return "8"

    def _l9132(self):
        self.prop[self.DOOR] = 0
        if self.obj == self.OIL:
            self.prop[self.DOOR] = 1
        self.spk = 113 + self.prop[self.DOOR]
        return "2011"

    def _l8140(self):  # eat, intransitive
        if not self._here(self.FOOD):
            return "8000"
        self._dstroy(self.FOOD)
        self.spk = 72
        return "2011"

    def _l9140(self):  # eat, transitive
        if self.obj == self.FOOD:
            self._dstroy(self.FOOD)
            self.spk = 72
            return "2011"
        if self.obj in (self.BIRD, self.SNAKE, self.CLAM, self.OYSTER,
                        self.DWARF, self.DRAGON, self.TROLL, self.BEAR):
            self.spk = 71
        return "2011"

    def _l9150(self):  # drink
        if (self.obj == 0 and self._liqloc(self.loc) != self.WATER
                and (self._liq() != self.WATER or not self._here(self.BOTTLE))):
            return "8000"
        if self.obj != 0 and self.obj != self.WATER:
            self.spk = 110
        if self.spk == 110 or self._liq() != self.WATER or not self._here(self.BOTTLE):
            return "2011"
        self.prop[self.BOTTLE] = 1
        self.place[self.WATER] = 0
        self.spk = 74
        return "2011"

    def _l9160(self):  # rub
        if self.obj != self.LAMP:
            self.spk = 76
        return "2011"

    def _l9170(self):  # throw
        if (self._toting(self.ROD2) and self.obj == self.ROD
                and not self._toting(self.ROD)):
            self.obj = self.ROD2
        if not self._toting(self.obj):
            return "2011"
        if 50 <= self.obj <= self.MAXTRS and self._at(self.TROLL):
            return "9178"
        if self.obj == self.FOOD and self._here(self.BEAR):
            return "9177"
        if self.obj != self.AXE:
            return "9020"
        for i in range(1, 6):
            if self.dloc[i] == self.loc:
                self._dwarf_axe_target = i
                return "9172"
        self.spk = 152
        if self._at(self.DRAGON) and self.prop[self.DRAGON] == 0:
            self._rspeak(self.spk)
            self._drop(self.AXE, self.loc)
            self.k = self.NULL
            return "8"
        self.spk = 158
        if self._at(self.TROLL):
            self._rspeak(self.spk)
            self._drop(self.AXE, self.loc)
            self.k = self.NULL
            return "8"
        if self._here(self.BEAR) and self.prop[self.BEAR] == 0:
            return "9176"
        self.obj = 0
        return "9120"

    def _l9172(self):
        i = self._dwarf_axe_target
        self.spk = 48
        if self.rng.ran(3) == 0 or self.saved != -1:
            self._rspeak(self.spk)
            self._drop(self.AXE, self.loc)
            self.k = self.NULL
            return "8"
        self.dseen[i] = False
        self.dloc[i] = 0
        self.spk = 47
        self.dkill += 1
        if self.dkill == 1:
            self.spk = 149
        self._rspeak(self.spk)
        self._drop(self.AXE, self.loc)
        self.k = self.NULL
        return "8"

    def _l9176(self):
        self.spk = 164
        self._drop(self.AXE, self.loc)
        self.fixed[self.AXE] = -1
        self.prop[self.AXE] = 1
        self._juggle(self.BEAR)
        return "2011"

    def _l9177(self):
        self.obj = self.BEAR
        return "9210"

    def _l9178(self):
        self.spk = 159
        self._drop(self.obj, 0)
        self._move(self.TROLL, 0)
        self._move(self.TROLL + 100, 0)
        self._drop(self.TROLL2, self.data.plac[self.TROLL])
        self._drop(self.TROLL2 + 100, self.data.fixd[self.TROLL])
        self._juggle(self.CHASM)
        return "2011"

    def _l8180(self):  # quit
        self.gaveup = self._yes(22, 54, 54)
        if self.gaveup:
            return "20000"
        return "2012"

    def _l9190(self):  # find / inventory-of-object
        if (self._at(self.obj) or (self._liq() == self.obj and self._at(self.BOTTLE))
                or self.k == self._liqloc(self.loc)):
            self.spk = 94
        for i in range(1, 6):
            if (self.dloc[i] == self.loc and self.dflag >= 2
                    and self.obj == self.DWARF):
                self.spk = 94
        if self.closed:
            self.spk = 138
        if self._toting(self.obj):
            self.spk = 24
        return "2011"

    def _l8200(self):  # inventory
        self.spk = 98
        for i in range(1, 101):
            if i == self.BEAR or not self._toting(i):
                continue
            if self.spk == 98:
                self._rspeak(99)
            self._pspeak(i, -1)
            self.spk = 0
        if self._toting(self.BEAR):
            self.spk = 141
        return "2011"

    def _l9210(self):  # feed
        if self.obj == self.BIRD:
            self.spk = 100
            return "2011"
        return "9212"

    def _l9212(self):
        if self.obj not in (self.SNAKE, self.DRAGON, self.TROLL):
            return "9213"
        self.spk = 102
        if self.obj == self.DRAGON and self.prop[self.DRAGON] != 0:
            self.spk = 110
        if self.obj == self.TROLL:
            self.spk = 182
        if self.obj != self.SNAKE or self.closed or not self._here(self.BIRD):
            return "2011"
        self.spk = 101
        self._dstroy(self.BIRD)
        self.prop[self.BIRD] = 0
        self.tally2 += 1
        return "2011"

    def _l9213(self):
        if self.obj != self.DWARF:
            return "9214"
        if not self._here(self.FOOD):
            return "2011"
        self.spk = 103
        self.dflag += 1
        return "2011"

    def _l9214(self):
        if self.obj != self.BEAR:
            return "9215"
        if self.prop[self.BEAR] == 0:
            self.spk = 102
        if self.prop[self.BEAR] == 3:
            self.spk = 110
        if not self._here(self.FOOD):
            return "2011"
        self._dstroy(self.FOOD)
        self.prop[self.BEAR] = 1
        self.fixed[self.AXE] = 0
        self.prop[self.AXE] = 0
        self.spk = 168
        return "2011"

    def _l9215(self):
        self.spk = 14
        return "2011"

    def _l9220(self):  # fill
        if self.obj == self.VASE:
            return "9222"
        if self.obj != 0 and self.obj != self.BOTTLE:
            return "2011"
        if self.obj == 0 and not self._here(self.BOTTLE):
            return "8000"
        self.spk = 107
        if self._liqloc(self.loc) == 0:
            self.spk = 106
        if self._liq() != 0:
            self.spk = 105
        if self.spk != 107:
            return "2011"
        self.prop[self.BOTTLE] = _mod(self.cond[self.loc], 4) // 2 * 2
        k = self._liq()
        if self._toting(self.BOTTLE):
            self.place[k] = -1
        if k == self.OIL:
            self.spk = 108
        return "2011"

    def _l9222(self):
        self.spk = 29
        if self._liqloc(self.loc) == 0:
            self.spk = 144
        if self._liqloc(self.loc) == 0 or not self._toting(self.VASE):
            return "2011"
        self._rspeak(145)
        self.prop[self.VASE] = 2
        self.fixed[self.VASE] = -1
        return "9024"

    def _l9230(self):  # blast
        if self.prop[self.ROD2] < 0 or not self.closed:
            return "2011"
        self.bonus = 133
        if self.loc == 115:
            self.bonus = 134
        if self._here(self.ROD2):
            self.bonus = 135
        self._rspeak(self.bonus)
        return "20000"

    def _l8240(self):  # score
        self.scorng = True
        return "20000"

    def _l8241(self):
        self.scorng = False
        self._emit("If you were to quit now, you would score{:4d} out of a "
                   "possible{:4d}.".format(self.score, self.mxscor))
        self.gaveup = self._yes(143, 54, 54)
        if self.gaveup:
            return "20000"
        return "2012"

    def _l8250(self):  # fee fie foe foo
        k = self._v(self.wd1, 3)
        self.spk = 42
        if self.foobar != 1 - k:
            if self.foobar != 0:
                self.spk = 151
            return "2011"
        self.foobar = k  # 8252
        if k != 4:
            return "2009"
        self.foobar = 0
        if (self.place[self.EGGS] == self.data.plac[self.EGGS]
                or (self._toting(self.EGGS) and self.loc == self.data.plac[self.EGGS])):
            return "2011"
        if (self.place[self.EGGS] == 0 and self.place[self.TROLL] == 0
                and self.prop[self.TROLL] == 0):
            self.prop[self.TROLL] = 1
        k = 2
        if self._here(self.EGGS):
            k = 1
        if self.loc == self.data.plac[self.EGGS]:
            k = 0
        self._move(self.EGGS, self.data.plac[self.EGGS])
        self._pspeak(self.EGGS, k)
        return "2012"

    def _l8260(self):  # brief
        self.spk = 156
        self.abbnum = 10000
        self.detail = 3
        return "2011"

    def _l8270(self):  # read, intransitive resolve
        if self._here(self.MAGZIN):
            self.obj = self.MAGZIN
        if self._here(self.TABLET):
            self.obj = self.obj * 100 + self.TABLET
        if self._here(self.MESSAG):
            self.obj = self.obj * 100 + self.MESSAG
        if self.closed and self._toting(self.OYSTER):
            self.obj = self.OYSTER
        if self.obj > 100 or self.obj == 0 or self._dark():
            return "8000"
        return "9270"

    def _l9270(self):  # read
        if self._dark():
            return "5100"
        if self.obj == self.MAGZIN:
            self.spk = 190
        if self.obj == self.TABLET:
            self.spk = 196
        if self.obj == self.MESSAG:
            self.spk = 191
        if self.obj == self.OYSTER and self.hinted[2] and self._toting(self.OYSTER):
            self.spk = 194
        if (self.obj != self.OYSTER or self.hinted[2] or not self._toting(self.OYSTER)
                or not self.closed):
            return "2011"
        self.hinted[2] = self._yes(192, 193, 54)
        return "2012"

    def _l9280(self):  # break
        if self.obj == self.MIRROR:
            self.spk = 148
        if self.obj == self.VASE and self.prop[self.VASE] == 0:
            self.spk = 198  # 9282
            if self._toting(self.VASE):
                self._drop(self.VASE, self.loc)
            self.prop[self.VASE] = 2
            self.fixed[self.VASE] = -1
            return "2011"
        if self.obj != self.MIRROR or not self.closed:
            return "2011"
        self._rspeak(197)
        return "19000"

    def _l9290(self):  # wake
        if self.obj != self.DWARF or not self.closed:
            return "2011"
        self._rspeak(199)
        return "19000"

    def _l8300(self):  # suspend (save is a backend concern; decline in-engine)
        self.spk = 201
        return "2011"

    def _l8310(self):  # hours (cave-hours dropped)
        self._mspeak(6)
        return "2012"

    # ---- clocks, closing, lamp --------------------------------------------

    def _l10000(self):
        self.prop[self.GRATE] = 0
        self.prop[self.FISSUR] = 0
        for i in range(1, 7):
            self.dseen[i] = False
            self.dloc[i] = 0
        self._move(self.TROLL, 0)
        self._move(self.TROLL + 100, 0)
        self._move(self.TROLL2, self.data.plac[self.TROLL])
        self._move(self.TROLL2 + 100, self.data.fixd[self.TROLL])
        self._juggle(self.CHASM)
        if self.prop[self.BEAR] != 3:
            self._dstroy(self.BEAR)
        self.prop[self.CHAIN] = 0
        self.fixed[self.CHAIN] = 0
        self.prop[self.AXE] = 0
        self.fixed[self.AXE] = 0
        self._rspeak(129)
        self.clock1 = -1
        self.closng = True
        return "19999"

    def _l11000(self):
        self.prop[self.BOTTLE] = self._put(self.BOTTLE, 115, 1)
        self.prop[self.PLANT] = self._put(self.PLANT, 115, 0)
        self.prop[self.OYSTER] = self._put(self.OYSTER, 115, 0)
        self.prop[self.LAMP] = self._put(self.LAMP, 115, 0)
        self.prop[self.ROD] = self._put(self.ROD, 115, 0)
        self.prop[self.DWARF] = self._put(self.DWARF, 115, 0)
        self.loc = 115
        self.oldloc = 115
        self.newloc = 115
        self._put(self.GRATE, 116, 0)
        self.prop[self.SNAKE] = self._put(self.SNAKE, 116, 1)
        self.prop[self.BIRD] = self._put(self.BIRD, 116, 1)
        self.prop[self.CAGE] = self._put(self.CAGE, 116, 0)
        self.prop[self.ROD2] = self._put(self.ROD2, 116, 0)
        self.prop[self.PILLOW] = self._put(self.PILLOW, 116, 0)
        self.prop[self.MIRROR] = self._put(self.MIRROR, 115, 0)
        self.fixed[self.MIRROR] = 116
        for i in range(1, 101):
            if self._toting(i):
                self._dstroy(i)
        self._rspeak(132)
        self.closed = True
        return "2"

    def _l12000(self):
        self._rspeak(188)
        self.prop[self.BATTER] = 1
        if self._toting(self.BATTER):
            self._drop(self.BATTER, self.loc)
        self.limit += 2500
        self.lmwarn = False
        return "19999"

    def _l12200(self):
        if self.lmwarn or not self._here(self.LAMP):
            return "19999"
        self.lmwarn = True
        self.spk = 187
        if self.place[self.BATTER] == 0:
            self.spk = 183
        if self.prop[self.BATTER] == 1:
            self.spk = 189
        self._rspeak(self.spk)
        return "19999"

    def _l12400(self):
        self.limit = -1
        self.prop[self.LAMP] = 0
        if self._here(self.LAMP):
            self._rspeak(184)
        return "19999"

    def _l12600(self):
        self._rspeak(185)
        self.gaveup = True
        return "20000"

    def _l13000(self):  # demo end (unused; demo is always False)
        self._mspeak(1)
        return "20000"

    def _l19000(self):  # disturbed the dwarves during closing -> death
        self._rspeak(136)
        return "20000"

    # ---- scoring / exit ----------------------------------------------------

    def compute_score(self):
        """Return ``(score, max_score)`` for the current state (no side effects).

        Mirrors the tally in FORTRAN label 20000; used both by the exit/score
        path and to report a live score in structured state.
        """
        score = 0
        mxscor = 0
        for i in range(50, self.MAXTRS + 1):
            if i not in self.data.has_text:
                continue
            k = 12
            if i == self.CHEST:
                k = 14
            if i > self.CHEST:
                k = 16
            if self.prop[i] >= 0:
                score += 2
            if self.place[i] == 3 and self.prop[i] == 0:
                score += k - 2
            mxscor += k
        score += (self.maxdie - self.numdie) * 10
        mxscor += self.maxdie * 10
        if not (self.scorng or self.gaveup):
            score += 4
        mxscor += 4
        if self.dflag != 0:
            score += 25
        mxscor += 25
        if self.closng:
            score += 25
        mxscor += 25
        if self.closed:
            if self.bonus == 0:
                score += 10
            if self.bonus == 135:
                score += 25
            if self.bonus == 134:
                score += 30
            if self.bonus == 133:
                score += 45
        mxscor += 45
        if self.place[self.MAGZIN] == 108:
            score += 1
        mxscor += 1
        score += 2
        mxscor += 2
        for i in range(1, self.data.hntmax + 1):
            if self.hinted[i]:
                score -= self.data.hints[i][1]
        return score, mxscor

    # ---- structured state (for web / MCP consumers) -----------------------

    def visible_objects(self):
        """Object numbers visible at the current location (none if dark)."""
        if self._dark():
            return []
        seen, result = set(), []
        i = self.atloc[self.loc]
        while i != 0:
            obj = i if i <= 100 else i - 100
            if obj not in seen:
                seen.add(obj)
                result.append(obj)
            i = self.link[i]
        return result

    def inventory_objects(self):
        """Object numbers currently being carried."""
        return [o for o in range(1, 101) if self.place[o] == -1]

    def available_motions(self):
        """Motion keywords with an exit from the current location.

        Includes hidden/secret passages -- it reads the raw travel table -- so
        treat it as a map aid, not something the original game would volunteer.
        """
        key = self.data.key.get(self.loc, 0)
        if not key:
            return []
        verbs, kk = [], key
        while True:
            entry = self.data.travel[kk]
            v = abs(entry) % 1000
            if v != 1 and v not in verbs:
                verbs.append(v)
            if entry < 0:
                break
            kk += 1
        words = []
        for v in verbs:
            w = self.data.motion_words(v)
            if w:
                words.append(w[0])
        return words

    def _obj_ref(self, obj: int) -> dict:
        """Display name plus the command word for an object (word may be None)."""
        return {"name": self.data.object_name(obj), "word": self.data.object_word(obj)}

    def state(self) -> dict:
        """A JSON-serialisable snapshot of the game for external consumers."""
        loc = self.loc
        score, mxscor = self.compute_score()
        long = self.data.long_desc.get(loc, "")
        short = self.data.short_desc.get(loc)
        name = (short or long or "").split("\n", 1)[0]
        return {
            "location": loc,
            "name": name,
            "description": long,
            "dark": self._dark(),
            "visible_objects": [self._obj_ref(o) for o in self.visible_objects()],
            "inventory": [self._obj_ref(o) for o in self.inventory_objects()],
            "exits": self.available_motions(),
            "score": score,
            "max_score": mxscor,
            "turns": self.turns,
            "carrying": self.holdng,
            "lamp_on": self.prop[self.LAMP] == 1,
            "closing": self.closng,
            "closed": self.closed,
            "ended": False,
        }

    def _l20000(self):
        score, mxscor = self.compute_score()
        self.score = score
        self.mxscor = mxscor
        if self.scorng:
            return "8241"
        self._emit("You scored{:4d} out of a possible{:4d}, using{:5d} "
                   "turns.".format(score, mxscor, self.turns))
        self._final_rating(score)
        raise _GameOver

    def _final_rating(self, score):
        ctext = self.data.ctext
        cval = self.data.cval
        for i in range(len(cval)):
            if cval[i] >= score:
                self._speak(ctext[i])
                if i == len(cval) - 1:
                    self._emit("To achieve the next higher rating would be a "
                               "neat trick!\n\nCongratulations!!")
                    return
                need = cval[i] + 1 - score
                pts = "." if need == 1 else "s."
                self._emit("To achieve the next higher rating, you need{:3d} "
                           "more point{}".format(need, pts))
                return
        self._emit("You just went off my scale!!")


def new_game(seed: int | None = None) -> Game:
    return Game(load_default_data(), seed=seed)
