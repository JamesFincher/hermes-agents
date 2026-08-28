#!/usr/bin/env python3
"""Print the playbook §10 review heuristics. No network."""

from __future__ import annotations

HEURISTICS = [
    "What is in context on turn 40?",
    "What does the second call to the same expensive thing cost?",
    "Which rules are prompted that could be enforced?",
    "What happens when the primary dependency is down?",
    "What survives /new?",
    "What do the children return?",
    "Where does untrusted text enter, and what is between it and the terminal?",
    "What would this profile confidently get wrong?",
    "Which surface is doing the most work?",
]


def main() -> int:
    for index, line in enumerate(HEURISTICS, start=1):
        print(f"{index}. {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
