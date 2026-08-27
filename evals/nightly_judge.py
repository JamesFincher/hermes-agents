#!/usr/bin/env python3
"""On-demand mechanical rubric. Not a scheduled nightly LLM judge.

A host cron may set HDR_JUDGE_MODEL. This repo does not invent a model id
or a GitHub Actions secret. Skip when HDR_JUDGE_MODEL is unset.

When HDR_JUDGE_MODEL is set, score the 12-question offline loop with the
mechanical rubric (always) and optionally invoke HDR_JUDGE_CMD with a JSON
payload on stdin. Do not invent a model id or an HTTP provider.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.rubric import score_brief
from evals.run_offline import run_all


def main() -> int:
    model = os.environ.get("HDR_JUDGE_MODEL")
    if not model:
        print(json.dumps({"skipped": True, "reason": "HDR_JUDGE_MODEL unset; on-demand mechanical only"}))
        return 0
    payload = run_all()
    rows = []
    scores: list[float] = []
    for row in payload.get("results") or []:
        scored = score_brief(
            brief=str(row.get("brief") or ""),
            kind=str(row.get("kind") or "survey"),
            gate_errors=list(row.get("gate_errors") or []),
        )
        rows.append(
            {
                "id": row.get("id"),
                "kind": row.get("kind"),
                "tier": row.get("tier"),
                "mean": scored["mean"],
                "dims": scored["dims"],
                "gate_errors": row.get("gate_errors") or [],
            }
        )
        scores.append(float(scored["mean"]))
    mean = sum(scores) / len(scores) if scores else 0.0
    clean = all(not (row.get("gate_errors") or []) for row in payload.get("results") or [])
    report = {
        "ok": payload.get("completed") == payload.get("total") == 12 and mean >= 2.4 and clean,
        "judge_model": model,
        "completed": payload.get("completed"),
        "total": payload.get("total"),
        "rubric_mean": mean,
        "results": rows,
        "note": (
            "On-demand mechanical rubric. Not a nightly LLM judge. "
            "Set HDR_JUDGE_CMD to a host command that reads this JSON on stdin "
            "if you want a second-model pass. Official MoA is a provider, not a toolset. "
            "Do not invent a model id or a GitHub Actions secret."
        ),
    }
    cmd = os.environ.get("HDR_JUDGE_CMD")
    if cmd:
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(report),
                text=True,
                capture_output=True,
                check=False,
                shell=True,
            )
            report["judge_cmd_exit"] = proc.returncode
            report["judge_cmd_stdout"] = (proc.stdout or "")[:4000]
        except OSError as exc:
            report["ok"] = False
            report["error"] = f"HDR_JUDGE_CMD failed: {exc}"
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
