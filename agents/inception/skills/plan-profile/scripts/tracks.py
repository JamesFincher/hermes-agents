#!/usr/bin/env python3
"""Print the four investigation tracks check_plan requires."""

from __future__ import annotations

TRACKS = ("tool", "skill", "mcp", "plugin")


def main() -> int:
    print("required_tracks=" + ",".join(TRACKS))
    print("mcp_and_plugin_may_reject=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
