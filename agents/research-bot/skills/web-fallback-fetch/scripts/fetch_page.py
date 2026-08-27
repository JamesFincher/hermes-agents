#!/usr/bin/env python3
"""Fetch a URL to stdout. No shell pipe. Strips a few tags."""

from __future__ import annotations

import re
import sys
import urllib.request


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_page.py <url>", file=sys.stderr)
        return 1
    url = sys.argv[1]
    request = urllib.request.Request(url, headers={"User-Agent": "hdr-research-bot/2.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 1
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    sys.stdout.write(text.strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
