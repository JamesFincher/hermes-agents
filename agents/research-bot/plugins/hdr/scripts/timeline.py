#!/usr/bin/env python3
"""Sort dated lines. Input: YYYY-MM-DD<TAB>event."""

from __future__ import annotations

import sys


def main() -> int:
    rows = []
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        rows.append(raw)
    rows.sort()
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
