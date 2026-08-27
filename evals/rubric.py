"""Mechanical end-state rubric. Nightly LLM judge is separate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from evals.gates import check_run

_SID = re.compile(r"\[S(\d+)\]")


def score_brief(
    *,
    brief: str,
    kind: str,
    gate_errors: list[str],
    word_count: int | None = None,
) -> dict[str, Any]:
    words = word_count if word_count is not None else len(brief.split())
    citation = 3 if not any("unresolvable" in e or "unsupported" in e for e in gate_errors) else 0
    if any("stat without marker" in e for e in gate_errors):
        citation = 0
    factual = 3 if citation == 3 and brief.strip() else 1
    coverage = 3 if _SID.search(brief) and len(brief.splitlines()) >= 3 else 1
    if kind == "contradiction":
        contradiction = 3 if re.search(r"disagree|stale|not an average|contradict", brief, re.I) else 1
    else:
        contradiction = 3
    if kind in {"no-source", "paywall", "dead-link"}:
        calibration = (
            3
            if re.search(r"did not find|paywall|archiv|404|no OA|not listed|no army", brief, re.I)
            else 1
        )
    else:
        calibration = 3 if "I did not find" in brief or _SID.search(brief) else 2
    concision = 3 if words <= 800 else 2 if words <= 1500 else 1
    dims = {
        "factual_accuracy": factual,
        "citation_validity": citation,
        "coverage": coverage,
        "contradiction_handling": contradiction,
        "calibration": calibration,
        "concision": concision,
    }
    mean = sum(dims.values()) / len(dims)
    return {"dims": dims, "mean": mean, "words": words, "gate_errors": gate_errors}


def score_run_dir(run_dir: Path, kind: str) -> dict[str, Any]:
    brief = (run_dir / "brief.md").read_text(encoding="utf-8")
    return score_brief(brief=brief, kind=kind, gate_errors=check_run(run_dir))
