"""Deterministic question-support matching. Shared by gap_scan and evidence_stats."""

from __future__ import annotations

import re
from typing import Any

from . import claims as claim_store

_TOKEN = re.compile(r"[a-z0-9]{4,}")
_STOP = frozenset(
    {
        "what",
        "when",
        "where",
        "which",
        "that",
        "this",
        "with",
        "from",
        "have",
        "been",
        "were",
        "they",
        "their",
        "about",
        "into",
        "than",
        "does",
        "will",
        "your",
        "only",
        "also",
        "over",
        "such",
        "then",
        "them",
        "these",
        "those",
        "being",
        "after",
        "before",
    }
)
_DATE = re.compile(r"(19\d{2}|20\d{2})(?:-(\d{2})(?:-(\d{2}))?)?")


def tokens(text: str) -> set[str]:
    return {part for part in _TOKEN.findall((text or "").lower()) if part not in _STOP}


def source_blob(source: dict[str, Any]) -> str:
    parts = [str(source.get("title") or ""), str(source.get("quote") or "")]
    for span in source.get("spans") or []:
        if isinstance(span, dict):
            parts.append(str(span.get("q") or ""))
    return " ".join(parts)


def mentions_question(source: dict[str, Any], question: str) -> bool:
    needle = (question or "").strip()
    if not needle:
        return False
    blob = source_blob(source).lower()
    if needle.lower() in blob:
        return True
    wanted = tokens(needle)
    if not wanted:
        return False
    have = tokens(blob)
    need = 2 if len(wanted) >= 2 else 1
    return len(wanted & have) >= need


def claim_links_question(node: dict[str, Any], question: str) -> bool:
    text = str(node.get("text") or "").strip()
    needle = (question or "").strip()
    if not text or not needle:
        return False
    lower_text = text.lower()
    lower_q = needle.lower()
    if lower_q in lower_text or lower_text in lower_q:
        return True
    wanted = tokens(needle)
    have = tokens(text)
    if not wanted:
        return False
    need = 2 if len(wanted) >= 2 else 1
    return len(wanted & have) >= need


def supporting_sources(
    question: str,
    sources: list[dict[str, Any]],
    graph: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    data = graph if graph is not None else claim_store.load_claims()
    linked_ids: set[str] = set()
    for node in data.values():
        if not isinstance(node, dict):
            continue
        if not claim_links_question(node, question):
            continue
        for edge in node.get("support") or []:
            if not isinstance(edge, dict):
                continue
            if edge.get("stance") != "supports":
                continue
            sid = str(edge.get("src") or "")
            if sid:
                linked_ids.add(sid)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        sid = str(source.get("id") or "")
        if sid and sid in seen:
            continue
        if mentions_question(source, question) or (sid and sid in linked_ids):
            if sid:
                seen.add(sid)
            out.append(source)
    return out


def independent_urls(sources: list[dict[str, Any]]) -> set[str]:
    urls: set[str] = set()
    for source in sources:
        url = str(source.get("canonical_url") or source.get("url") or "").strip()
        if url:
            urls.add(url)
    return urls


def question_coverage(
    question: str,
    sources: list[dict[str, Any]],
    graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    support = supporting_sources(question, sources, graph)
    by_tier: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    for source in support:
        tier = str(source.get("tier") or "D")
        by_tier[tier] = by_tier.get(tier, 0) + 1
    return {
        "q": question,
        "support": len(independent_urls(support)),
        "tiers": by_tier,
        "sources": support,
    }


def parse_ymd(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    match = _DATE.search(raw)
    if not match:
        return None
    year = match.group(1)
    month = match.group(2) or "01"
    day = match.group(3) or "01"
    return f"{year}-{month}-{day}"


def is_stale(published: Any, since: Any) -> bool:
    left = parse_ymd(published)
    right = parse_ymd(since)
    if not left or not right:
        return False
    return left < right
