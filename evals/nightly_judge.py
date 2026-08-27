#!/usr/bin/env python3
"""Nightly LLM judge. Not CI. Skip when no judge model is configured."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if not os.environ.get("HDR_JUDGE_MODEL"):
        print(json.dumps({"skipped": True, "reason": "HDR_JUDGE_MODEL unset; nightly only"}))
        return 0
    print(
        json.dumps(
            {
                "ok": False,
                "error": "LLM judge runner is host-configured. Rubric lives in evals/questions.json.",
            }
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
