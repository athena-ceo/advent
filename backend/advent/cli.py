# Copyright (c) 2026 Athena Decisions Systems SAS.
"""A minimal terminal front end for the Adventure engine.

    python -m advent            # play with a random seed
    python -m advent --seed 12  # reproducible game

The engine drives itself, calling back for input and emitting paragraphs of
output; this module just wires those callbacks to stdin/stdout.
"""
from __future__ import annotations

import argparse
import sys

from .game import Game


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play Colossal Cave Adventure.")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed the RNG for a reproducible game")
    args = parser.parse_args(argv)

    game = Game(seed=args.seed)

    def read_line() -> str:
        try:
            return input("\n> ")
        except EOFError:
            raise
        except KeyboardInterrupt:
            print()
            raise EOFError

    def write(text: str) -> None:
        print("\n" + text)

    try:
        game.run(read_line, write)
    except EOFError:
        pass
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
