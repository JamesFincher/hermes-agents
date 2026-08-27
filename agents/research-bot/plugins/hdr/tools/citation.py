"""claim_verify, conflict_report, cite_source v2."""

from __future__ import annotations

import re
from typing import Any

from ..runtime import citation_style, dump, error
from ..store import bus, claims, ledger


def claim_verify(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
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
        unsupported_parts = [claim]
        from ..store import spans as span_mod

        for source in sources:
            corpus = str(source.get("corpus") or "")
            if not corpus:
                continue
            digest = corpus.split("/")[-1].replace(".txt", "")
            page = bus.read_corpus(digest, offset=0, limit=2_000_000)
            if page.get("error"):
                continue
            check = span_mod.verify_claim(claim, str(page.get("text") or ""))
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
                "unsupported_parts": unsupported_parts,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def conflict_report(args: dict[str, Any], **kwargs: Any) -> str:
    del args, kwargs
    try:
        rows = claims.conflicts()
        return dump({"ok": True, "count": len(rows), "conflicts": rows})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def cite_source(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        style = str((args or {}).get("style") or citation_style()).lower()
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
