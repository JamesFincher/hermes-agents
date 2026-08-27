"""Deterministic brief from the ledger. Phase 5. No network. No prompt."""

from __future__ import annotations

import re
from typing import Any

from . import claims, ledger, run
from .support import source_supports_question

_STAT_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\b(19|20)\d{2}\b|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|“[^”]{3,}”|\"[^\"]{3,}\")"
)


def _plain(text: str) -> str:
    """Drop dates and quantities so the Citation Gate will accept a gap line."""
    cleaned = _STAT_RE.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -—,:;")
    return cleaned or "this question"


def _lead_line(lead: dict[str, Any], question: str) -> str:
    sid = str(lead.get("id") or "")
    quote = str(lead.get("quote") or lead.get("title") or "see card").strip()
    if sid:
        return f"{quote} [{sid}]."
    return f"I did not find a reliable source for {_plain(question)}."


def _gap_line(item: str) -> str:
    return f"- I did not find two independent sources for {_plain(str(item))}."


def draft_brief(current: dict[str, Any] | None = None) -> dict[str, Any]:
    state = current if current is not None else (run.load_run() or {})
    sources = ledger.list_sources(run_id=str(state.get("run_id") or ""))
    if not sources:
        sources = ledger.list_sources()
    conflicts = claims.conflicts()
    lines: list[str] = []
    question = str(state.get("question") or "Research question")
    primary = [src for src in sources if src.get("tier") in {"A", "B"}]
    lead = primary[0] if primary else (sources[0] if sources else None)
    if lead:
        lines.append(_lead_line(lead, question))
    else:
        lines.append(f"I did not find a reliable source for {_plain(question)}.")
    lines.append("")
    lines.append("Evidence")
    for src in sources:
        title = src.get("title") or src.get("canonical_url") or src.get("url")
        quote = src.get("quote") or ""
        sid = str(src.get("id") or "")
        bit = f"- {title}"
        if quote:
            bit += f" — {quote}"
        if sid:
            bit += f" [{sid}]"
        if src.get("fetch_status") == "paywall":
            bit += " (paywall; abstract only)"
        if src.get("archived_url"):
            bit += f" archived {src.get('archived_url')}"
        lines.append(bit)
    if conflicts:
        lines.append("")
        lines.append("Disagreement")
        for row in conflicts:
            label = _plain(str(row.get("text") or row.get("id") or "claim"))
            lines.append(f"- {label}: sources disagree. Do not average.")
    open_qs = list(state.get("open_questions") or [])
    unanswered: list[str] = []
    for question_item in open_qs:
        attached = [src for src in sources if source_supports_question(src, str(question_item))]
        independent = {src.get("canonical_url") or src.get("url") for src in attached}
        if len(independent) < 2:
            unanswered.append(str(question_item))
    if not sources:
        unanswered = [str(item) for item in (open_qs or [question])]
    if unanswered or not sources:
        lines.append("")
        lines.append("Not found")
        for item in unanswered or [question]:
            lines.append(_gap_line(item))
    text = "\n".join(lines).strip() + "\n"
    return {
        "ok": True,
        "brief": text,
        "sources": len(sources),
        "governor": state.get("governor"),
    }
