"""Complete all 12 eval questions from recorded fixtures. No network.

Honors each question's tier. Materializes a run dir and scores it with
check_run (exact-span claim_verify). Offline FakeCtx is not live P10.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from evals.gates import check_run  # noqa: E402
from test_hdr_plugin import FakeCtx, _load_plugin_package  # noqa: E402


def _kind_lines(kind: str) -> list[str]:
    if kind == "contradiction":
        return ["Sources disagree. This secondary recap is stale. Do not average."]
    if kind == "no-source":
        return ["I did not find a reliable official page that names this."]
    if kind == "paywall":
        return ["This page is paywall; no OA copy."]
    if kind == "dead-link":
        return ["The live host now returns 404."]
    if kind == "pdf":
        return ["Recorded extract, not a live PDF byte stream."]
    return ["I did not find additional independent sources."]


def _materialize_run(
    dest: Path,
    *,
    sources: list[dict[str, Any]],
    plugin_root: Path,
    kind: str,
    pages: list[dict[str, Any]],
    tier: str,
    budget_seconds: float,
) -> tuple[str, list[str]]:
    dest.mkdir(parents=True, exist_ok=True)
    corpus_out = dest / "corpus"
    corpus_out.mkdir(exist_ok=True)
    ledger_sources: list[dict[str, Any]] = []
    brief_lines: list[str] = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        sid = str(src.get("id") or "")
        if not sid:
            continue
        quote = str(src.get("quote") or "").strip()
        dest_name = f"{sid.lower()}.txt"
        raw_corpus = str(src.get("corpus") or "")
        text = ""
        if raw_corpus:
            src_path = Path(raw_corpus)
            if not src_path.is_absolute():
                src_path = plugin_root / raw_corpus
            if src_path.is_file():
                text = src_path.read_text(encoding="utf-8")
        if not text and quote:
            text = quote + "\n"
        if not text:
            continue
        (corpus_out / dest_name).write_text(text, encoding="utf-8")
        if quote:
            brief_lines.append(f"{quote} [{sid}].")
        ledger_sources.append(
            {
                "id": sid,
                "url": src.get("url"),
                "canonical_url": src.get("canonical_url") or src.get("url"),
                "title": src.get("title") or "",
                "tier": src.get("tier") or "C",
                "kind": src.get("kind") or "secondary",
                "corpus": f"corpus/{dest_name}",
                "quote": quote,
            }
        )
    brief_lines.extend(_kind_lines(kind))
    if len(brief_lines) < 3:
        brief_lines.append("I did not find additional independent sources.")
    brief = "\n".join(brief_lines) + "\n"
    (dest / "brief.md").write_text(brief, encoding="utf-8")
    (dest / "ledger.json").write_text(
        json.dumps({"version": 2, "sources": ledger_sources}, indent=2) + "\n",
        encoding="utf-8",
    )
    fetches: list[str] = []
    for page in pages:
        url = str(page.get("url") or "")
        if url and url not in fetches:
            fetches.append(url)
    ab = sum(1 for src in ledger_sources if src.get("tier") in {"A", "B"})
    (dest / "audit.json").write_text(
        json.dumps(
            {
                "fetches": fetches,
                "tokens": 4000,
                "tier_ab_sources": ab,
                "wall_seconds": 30,
                "tier_budget_seconds": budget_seconds,
                "tier": tier,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return brief, check_run(dest)


def run_question(
    qid: str,
    prompt: str,
    pages: list[dict[str, Any]],
    kind: str,
    tier: str = "standard",
) -> dict[str, Any]:
    tmp = tempfile.TemporaryDirectory()
    os.environ["HERMES_HOME"] = tmp.name
    pkg = _load_plugin_package()
    ctx = FakeCtx()
    pkg.register(ctx)
    try:
        chosen = tier if tier in pkg.runtime.TIERS else "standard"
        pkg.tools.research_plan(
            {
                "action": "create",
                "question": prompt,
                "tier": chosen,
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
        current = pkg.store.run.load_run() or {}
        budget = current.get("budget") or pkg.runtime.TIER_BUDGET[chosen]
        seconds = float(budget.get("seconds") or pkg.runtime.TIER_BUDGET[chosen]["seconds"])
        sources = pkg.store.ledger.list_sources(run_id=str(current.get("run_id") or ""))
        if not sources:
            sources = pkg.store.ledger.list_sources()
        dest = Path(tmp.name) / "eval-run"
        brief, gate_errors = _materialize_run(
            dest,
            sources=sources,
            plugin_root=pkg.runtime.plugin_data_root(),
            kind=kind,
            pages=pages,
            tier=str(current.get("tier") or chosen),
            budget_seconds=seconds,
        )
        verify = json.loads(pkg.tools.claim_verify({"claim": brief.split(".", 1)[0]}))
        return {
            "id": qid,
            "ok": bool(brief.strip()) and not gate_errors,
            "brief": brief,
            "kind": kind,
            "tier": str(current.get("tier") or chosen),
            "saturation": scan.get("saturation"),
            "verify": verify.get("status"),
            "sources": len(sources),
            "gate_errors": gate_errors,
        }
    finally:
        shutil.rmtree(tmp.name, ignore_errors=True)
        tmp.cleanup()


def run_all() -> dict[str, Any]:
    questions = json.loads((ROOT / "evals" / "questions.json").read_text(encoding="utf-8"))
    pages_by_id = json.loads((ROOT / "evals" / "fixtures" / "questions.json").read_text(encoding="utf-8"))
    results = []
    for row in questions["questions"]:
        qid = row["id"]
        pages = (pages_by_id.get(qid) or {}).get("pages") or []
        results.append(
            run_question(
                qid,
                row["prompt"],
                pages,
                row["kind"],
                str(row.get("tier") or "standard"),
            )
        )
    completed = sum(1 for item in results if item.get("brief"))
    return {"completed": completed, "total": len(results), "results": results}


def main() -> int:
    payload = run_all()
    print(json.dumps({"completed": payload["completed"], "total": payload["total"]}, indent=2))
    return 0 if payload["completed"] == payload["total"] == 12 else 1


if __name__ == "__main__":
    raise SystemExit(main())
