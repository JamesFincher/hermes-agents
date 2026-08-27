#!/usr/bin/env python3
"""Canonicalize and dedupe URLs. Deterministic. No model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parents[1]
if str(_PLUGIN) not in sys.path:
    sys.path.insert(0, str(_PLUGIN))

from store.urls import canonicalize  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Dedupe URLs by canonical form.")
    parser.add_argument("paths", nargs="*", help="Files of URLs, one per line. stdin if omitted.")
    args = parser.parse_args()
    lines: list[str] = []
    if args.paths:
        for path in args.paths:
            lines.extend(Path(path).read_text(encoding="utf-8").splitlines())
    else:
        lines.extend(sys.stdin.read().splitlines())
    seen: dict[str, str] = {}
    for raw in lines:
        url = raw.strip()
        if not url or url.startswith("#"):
            continue
        key = canonicalize(url) or url
        seen.setdefault(key, url)
    for url in seen.values():
        print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
