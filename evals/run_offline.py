"""Complete all 12 eval questions from recorded fixtures. No network."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from evals.gates import check_brief_against_plugin  # noqa: E402
from test_hdr_plugin import FakeCtx, _load_plugin_package  # noqa: E402


def run_question(qid: str, prompt: str, pages: list[dict[str, Any]], kind: str) -> dict[str, Any]:
    tmp = tempfile.TemporaryDirectory()
    os.environ["HERMES_HOME"] = tmp.name
    pkg = _load_plugin_package()
    ctx = FakeCtx()
    pkg.register(ctx)
    try:
        pkg.tools.research_plan(
            {
                "action": "create",
                "question": prompt,
                "tier": "standard",
                "open_questions": [prompt],
            }
        )
        for page in pages:
            pkg.hooks.transform_tool_result(
                "web_extract",
                {"url": page["url"], "text": page["text"], "title": page.get("title")},
                {"url": page["url"]},
            )
            extra = {k: page[k] for k in ("archived_url", "fetch_status") if page.get(k)}
            if extra:
                pkg.store.ledger.add_source({"url": page["url"], **extra})
        if kind == "contradiction" and len(pages) >= 2:
            pkg.store.claims.upsert_claim(
                "moa toolset exists", src="S1", stance="contradicts", conf=0.9
            )
            pkg.store.claims.upsert_claim(
                "moa toolset exists", src="S2", stance="supports", conf=0.4
            )
        scan = json.loads(pkg.tools.gap_scan({"detail": "summary"}))
        draft = pkg.store.draft.draft_brief()
        brief = str(draft.get("brief") or "")
        first = brief.split("\n", 1)[0]
        verify = json.loads(pkg.tools.claim_verify({"claim": first}))
        gate_errors = check_brief_against_plugin(brief, pkg)
        return {
            "id": qid,
            "ok": bool(brief.strip()),
            "brief": brief,
            "kind": kind,
            "saturation": scan.get("saturation"),
            "verify": verify.get("status"),
            "sources": draft.get("sources"),
            "gate_errors": gate_errors,
        }
    finally:
        tmp.cleanup()


def run_all() -> dict[str, Any]:
    questions = json.loads((ROOT / "evals" / "questions.json").read_text(encoding="utf-8"))
    pages_by_id = json.loads((ROOT / "evals" / "fixtures" / "questions.json").read_text(encoding="utf-8"))
    results = []
    for row in questions["questions"]:
        qid = row["id"]
        pages = (pages_by_id.get(qid) or {}).get("pages") or []
        results.append(run_question(qid, row["prompt"], pages, row["kind"]))
    completed = sum(1 for item in results if item.get("ok") and item.get("brief"))
    return {"completed": completed, "total": len(results), "results": results}


def main() -> int:
    payload = run_all()
    print(json.dumps({"completed": payload["completed"], "total": payload["total"]}, indent=2))
    return 0 if payload["completed"] == payload["total"] == 12 else 1


if __name__ == "__main__":
    raise SystemExit(main())
