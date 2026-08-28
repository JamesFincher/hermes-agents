#!/usr/bin/env python3
"""Exit 0 if the name may be a profile directory. Exit 1 with a reason."""

from __future__ import annotations

import sys

RESERVED = {"hermes", "test", "tmp", "root", "sudo"}
OUROBOROS = {"echo", "archive", "seatbelt", "council", "autopilot", "forge"}
FOREIGN = {"hdr", "research-bot", "inception"}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: reserved_names.py <name>", file=sys.stderr)
        return 2
    name = argv[1].strip().lower()
    if name in RESERVED:
        print(f"reserved profile name: {name}")
        return 1
    if name in OUROBOROS:
        print(f"ouroboros plugin-name collision: {name}")
        return 1
    if name in FOREIGN:
        print(f"forbidden profile name: {name}")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
