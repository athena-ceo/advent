# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Faithful Python port of the original 350-point Colossal Cave Adventure.

Ported from the PDP-10 FORTRAN source (advent.for) and data file (advent.dat)
by Crowther & Woods.  The data file is the authoritative game content; see
``advent.data`` for the parser and ``advent.game`` for the engine.
"""
from .data import GameData, load_default_data

__all__ = ["GameData", "load_default_data"]
