"""claim_verify, conflict_report, cite_source v2, citation_pass."""

from __future__ import annotations

import re
from typing import Any

from ..runtime import CITATION_STYLES, citation_style, dump, error, get_ctx
from ..store import bus, claims, ledger
from ..store import spans as span_mod

_MAP_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text"],
            },
        }
    },
    "required": ["claims"],
}


def _quote_text(source: dict[str, Any]) -> str:
    bits = [
        str(item.get("q") or "")
        for item in (source.get("spans") or [])
        if isinstance(item, dict) and item.get("q")
    ]
    if bits:
        return " ".join(bits)
    return str(source.get("quote") or "")


def _read_source_text(source: dict[str, Any]) -> str:
    corpus = str(source.get("corpus") or "")
    if not corpus:
        return ""
    digest = corpus.split("/")[-1].replace(".txt", "")
    page = bus.read_corpus(digest, offset=0, limit=8_000_000)
    if page.get("error"):
        return ""
    return str(page.get("text") or "")


def _record_graph(claim: str, evidence: list[dict[str, Any]], stance: str) -> list[str]:
    cids: list[str] = []
    for item in evidence:
        src = str(item.get("src") or "")
        if not src:
            continue
        result = claims.upsert_claim(
            claim,
            src=src,
            stance=stance,
            conf=0.9 if item.get("numeric_match") and item.get("entity_match") else 0.6,
            span=0,
        )
        if result.get("id"):
            cids.append(str(result["id"]))
    return cids


def _verify_one(claim: str, sources: list[dict[str, Any]], stance: str) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    parts: list[str] = []
    for source in sources:
        page = _read_source_text(source)
        if not page:
            continue
        check = span_mod.verify_claim(claim, page, quote_text=_quote_text(source))
        if not check.get("exact"):
            continue
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
        parts.extend(str(item) for item in (check.get("unsupported_parts") or []))
    status = "unsupported"
    unsupported_parts = [claim]
    cids: list[str] = []
    if evidence:
        if all(item.get("numeric_match") and item.get("entity_match") for item in evidence):
            status = "supported"
            unsupported_parts = []
        else:
            status = "partial"
            unsupported_parts = list(dict.fromkeys(parts)) or [claim]
        cids = _record_graph(claim, evidence, stance)
    return {
        "ok": True,
        "status": status,
        "evidence": evidence,
        "unsupported_parts": unsupported_parts,
        "claim_ids": cids,
    }


def claim_verify(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        claim = span_mod.cited_claim_text(str((args or {}).get("claim") or ""))
        if not claim:
            return error("claim is required")
        wanted = (args or {}).get("candidate_sources")
        sources = ledger.list_sources()
        if isinstance(wanted, list) and wanted:
            allow = {str(item) for item in wanted}
            sources = [src for src in sources if src.get("id") in allow]
        stance = str((args or {}).get("stance") or "supports")
        return dump(_verify_one(claim, sources, stance))
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
        needs_backfill = []
        for index, source in enumerate(sources, start=1):
            text, incomplete = _format(source, style)
            citations.append(
                {
                    "id": source.get("id"),
                    "n": index,
                    "text": text,
                    "url": source.get("canonical_url") or source.get("url"),
                    "container": source.get("container") or "",
                }
            )
            if incomplete:
                needs_backfill.append(source.get("id"))
        return dump(
            {
                "ok": True,
                "style": style,
                "count": len(citations),
                "citations": citations,
                "missing_ids": missing,
                "needs_backfill": needs_backfill,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def citation_pass(args: dict[str, Any], **kwargs: Any) -> str:
    """Map claims, then run claim_verify. Uses ctx.llm when the host exposes it."""
    del kwargs
    try:
        draft = str((args or {}).get("draft") or (args or {}).get("text") or "")
        if not draft:
            return error("draft is required")
        mapped, llm_used = _map_claims(draft)
        results = []
        unsupported = 0
        for row in mapped:
            claim = span_mod.cited_claim_text(str(row.get("text") or ""))
            if len(claim) < 12:
                continue
            wanted = row.get("sources")
            payload: dict[str, Any] = {"claim": claim}
            if isinstance(wanted, list) and wanted:
                payload["candidate_sources"] = [str(item) for item in wanted]
            verified = _verify_one(
                claim,
                [
                    src
                    for src in ledger.list_sources()
                    if not payload.get("candidate_sources")
                    or src.get("id") in set(payload["candidate_sources"])
                ],
                "supports",
            )
            if verified.get("status") == "unsupported":
                unsupported += 1
            results.append({"claim": claim, **verified})
        return dump(
            {
                "ok": True,
                "llm": llm_used,
                "count": len(results),
                "unsupported": unsupported,
                "results": results,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def _map_claims(draft: str) -> tuple[list[dict[str, Any]], bool]:
    llm = getattr(get_ctx(), "llm", None)
    structured = getattr(llm, "complete_structured", None) if llm is not None else None
    if callable(structured):
        try:
            result = structured(
                instructions=(
                    "Map each factual sentence to ledger ids such as S1. "
                    "Do not invent sources. If a sentence has [S#], keep those ids."
                ),
                input=[{"type": "text", "text": draft}],
                json_schema=_MAP_SCHEMA,
                schema_name="hdr.citation-map",
                purpose="hdr.citation-pass",
                temperature=0.0,
                max_tokens=800,
            )
            parsed = getattr(result, "parsed", None)
            if isinstance(parsed, dict) and isinstance(parsed.get("claims"), list):
                return parsed["claims"], True
        except Exception:
            pass
    rows: list[dict[str, Any]] = []
    for sentence in span_mod.split_cited_sentences(draft):
        line = sentence.strip()
        if len(line) < 20:
            continue
        markers = span_mod.claim_markers(line)
        rows.append({"text": line, "sources": markers})
    return rows, False


def _format(source: dict[str, Any], style: str) -> tuple[str, bool]:
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
    container = str(source.get("container") or "")
    incomplete = not author or not year
    if style == "ieee":
        who = f"{author}, " if author else ""
        year_bit = f", {year}" if year else ""
        box = f", {container}" if container else ""
        return f"{who}{title}{box}{year_bit}. {url}".strip(), incomplete
    if style == "chicago":
        who = f"{author}. " if author else ""
        year_bit = f" ({year})" if year else ""
        box = f" {container}." if container else ""
        pub = f" {publisher}." if publisher and publisher != container else ""
        return f'{who}"{title}"{year_bit}.{box}{pub} {url}'.strip(), incomplete
    who = f"{author} " if author else ""
    year_bit = f"({year}). " if year else ""
    box = f"{container}. " if container else ""
    pub = f"{publisher}. " if publisher and publisher != container else ""
    return f"{who}{year_bit}{title}. {box}{pub}{url}".strip(), incomplete
