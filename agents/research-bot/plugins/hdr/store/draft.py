"""Deterministic brief from the ledger. Phase 5. No network. No prompt."""

from __future__ import annotations

from typing import Any

from . import claims, ledger, run


def draft_brief() -> dict[str, Any]:
    current = run.load_run() or {}
    sources = ledger.list_sources(run_id=str(current.get("run_id") or ""))
    if not sources:
        sources = ledger.list_sources()
    conflicts = claims.conflicts()
    lines: list[str] = []
    question = str(current.get("question") or "Research question")
    primary = [src for src in sources if src.get("tier") in {"A", "B"}]
    lead = primary[0] if primary else (sources[0] if sources else None)
    if lead:
        quote = str(lead.get("quote") or lead.get("title") or "see card")
        lines.append(f"{quote} [{lead.get('id')}].")
    else:
        lines.append(f"I did not find a reliable source for: {question}.")
    lines.append("")
    lines.append("Evidence")
    for src in sources:
        title = src.get("title") or src.get("canonical_url") or src.get("url")
        quote = src.get("quote") or ""
        bit = f"- {title}"
        if quote:
            bit += f" — {quote}"
        bit += f" [{src.get('id')}]"
        if src.get("fetch_status") == "paywall":
            bit += " (paywall; abstract only)"
        if src.get("archived_url"):
            bit += f" archived {src.get('archived_url')}"
        lines.append(bit)
    if conflicts:
        lines.append("")
        lines.append("Disagreement")
        for row in conflicts:
            lines.append(f"- {row.get('text') or row.get('id')}: sources disagree. Do not average.")
    open_qs = list(current.get("open_questions") or [])
    unanswered = [
        q
        for q in open_qs
        if sum(1 for src in sources if src.get("tier") in {"A", "B"}) < 2
    ]
    if not sources:
        unanswered = open_qs or [question]
    if unanswered or not sources:
        lines.append("")
        lines.append("Not found")
        for item in unanswered or [question]:
            lines.append(f"- I did not find two independent sources for: {item}")
    text = "\n".join(lines).strip() + "\n"
    return {
        "ok": True,
        "brief": text,
        "sources": len(sources),
        "governor": current.get("governor"),
    }
