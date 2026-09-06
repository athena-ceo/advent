# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Random-number source for the engine.

The FORTRAN used its own linear-congruential ``RAN`` seeded from the clock.
We don't reproduce that exact stream (there is no value in bit-matching a
1977 PDP-10 clock), but we expose the same two primitives the game relies on
-- ``ran(range)`` (uniform 0..range-1) and ``pct(n)`` (true n% of the time) --
backed by a seedable :class:`random.Random` so games are reproducible.
"""
from __future__ import annotations

import random


class Rng:
    def __init__(self, seed: int | None = None):
        self._r = random.Random(seed)

    def ran(self, range_: int) -> int:
        """Uniform integer in ``0..range_-1`` (0 if range_ <= 1), like ``RAN``."""
        if range_ <= 1:
            self._r.random()  # still consume a draw, mirroring RAN(1) "kicks"
            return 0
        return self._r.randrange(range_)

    def pct(self, n: int) -> bool:
        """True ``n`` percent of the time (``PCT(N) = RAN(100) < N``)."""
        return self.ran(100) < n
