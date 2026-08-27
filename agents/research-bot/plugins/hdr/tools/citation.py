"""claim_verify, conflict_report, cite_source v2."""

from __future__ import annotations

import re
from typing import Any

from ..runtime import CITATION_STYLES, citation_style, dump, error
from ..store import bus, claims, ledger
from ..store import spans as span_mod


def _stance_from_check(check: dict[str, Any]) -> str:
    if check.get("exact"):
        return "supports"
    if check.get("entity_match") and check.get("numeric_match") is False:
        return "contradicts"
    return "silent"


def claim_verify(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        claim = str((args or {}).get("claim") or "").strip()
        if not claim:
            return error("claim is required")
        wanted = (args or {}).get("candidate_sources")
        sources = ledger.list_sources()
        if isinstance(wanted, list) and wanted:
            allow = {str(item) for item in wanted}
            sources = [src for src in sources if src.get("id") in allow]
        evidence = []
        partials = []
        unsupported_parts = [claim]
        for source in sources:
            corpus = str(source.get("corpus") or "")
            if not corpus:
                continue
            digest = corpus.split("/")[-1].replace(".txt", "")
            page = bus.read_corpus(digest, offset=0, limit=2_000_000)
            if page.get("error"):
                continue
            check = span_mod.verify_claim(claim, str(page.get("text") or ""))
            sid = str(source.get("id") or "")
            stance = _stance_from_check(check)
            span_off = check.get("off") if check.get("exact") else check.get("partial_off")
            if sid:
                claims.upsert_claim(
                    claim,
                    src=sid,
                    stance=stance,
                    span=int(span_off) if isinstance(span_off, int) else None,
                )
            if check.get("exact"):
                evidence.append(
                    {
                        "src": source.get("id"),
                        "off": check.get("off"),
                        "len": check.get("len"),
                        "exact": True,
                        "numeric_match": check.get("numeric_match"),
                        "entity_match": check.get("entity_match"),
                        "span": check.get("span"),
                    }
                )
            elif check.get("partial_span"):
                partials.append(
                    {
                        "src": source.get("id"),
                        "partial_span": check.get("partial_span"),
                        "partial_off": check.get("partial_off"),
                        "exact": False,
                    }
                )
        status = "unsupported"
        if evidence:
            if all(item.get("numeric_match") and item.get("entity_match") for item in evidence):
                status = "supported"
                unsupported_parts = []
            else:
                status = "partial"
        return dump(
            {
                "ok": True,
                "status": status,
                "evidence": evidence,
                "partial_spans": partials,
                "unsupported_parts": unsupported_parts,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def conflict_report(args: dict[str, Any], **kwargs: Any) -> str:
    del args
    task_id = kwargs.get("task_id")
    del task_id
    try:
        rows = claims.conflicts()
        return dump({"ok": True, "count": len(rows), "conflicts": rows})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def cite_source(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        raw_style = (args or {}).get("style")
        if raw_style not in (None, ""):
            style = str(raw_style).lower()
            if style not in CITATION_STYLES:
                return error("style must be apa, ieee, or chicago")
        else:
            style = citation_style()
        ids = (args or {}).get("ids")
        sources = ledger.list_sources()
        if isinstance(ids, list) and ids:
            allow = {str(item) for item in ids}
            sources = [src for src in sources if src.get("id") in allow]
            missing = sorted(allow - {str(src.get("id")) for src in sources})
        else:
            missing = []
        citations = []
        for index, source in enumerate(sources, start=1):
            citations.append(
                {
                    "id": source.get("id"),
                    "n": index,
                    "text": _format(source, style),
                    "url": source.get("canonical_url") or source.get("url"),
                }
            )
        return dump(
            {
                "ok": True,
                "style": style,
                "count": len(citations),
                "citations": citations,
                "missing_ids": missing,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def _format(source: dict[str, Any], style: str) -> str:
    authors = source.get("authors") or []
    author = ", ".join(str(item) for item in authors[:3]) if authors else ""
    title = str(source.get("title") or source.get("url") or "Untitled")
    year = ""
    published = str(source.get("published") or source.get("retrieved") or "")
    match = re.search(r"(20\d{2}|19\d{2})", published)
    if match:
        year = match.group(1)
    url = str(source.get("canonical_url") or source.get("url") or "")
    publisher = str(source.get("publisher") or "")
    if style == "ieee":
        who = f"{author}, " if author else ""
        year_bit = f", {year}" if year else ""
        return f"{who}{title}{year_bit}. {url}".strip()
    if style == "chicago":
        who = f"{author}. " if author else ""
        year_bit = f" ({year})" if year else ""
        pub = f" {publisher}." if publisher else ""
        return f'{who}"{title}"{year_bit}.{pub} {url}'.strip()
    who = f"{author} " if author else ""
    year_bit = f"({year}). " if year else ""
    pub = f"{publisher}. " if publisher else ""
    return f"{who}{year_bit}{title}. {pub}{url}".strip()
