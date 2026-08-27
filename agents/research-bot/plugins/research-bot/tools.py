"""research-bot source ledger tools. Handlers never raise; always return JSON."""

from __future__ import annotations

import json
from typing import Any

from . import ledger, runtime


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True)


def source_ledger_add(args: dict[str, Any], **kwargs: Any) -> str:
    """Record a retrieved source. Call after web_search / web_extract / Context7."""
    del kwargs
    try:
        url = str(args.get("url") or "").strip()
        if not url:
            return _dumps({"error": "url is required"})
        title = str(args.get("title") or "").strip()
        quote = str(args.get("quote") or "").strip()
        kind = str(args.get("kind") or "web").strip() or "web"
        origin = str(args.get("retrieved_via") or args.get("origin") or "tool").strip()
        return _dumps(
            ledger.add_source(
                url=url,
                title=title or url,
                quote=quote,
                kind=kind,
                origin=origin,
            )
        )
    except Exception as exc:  # noqa: BLE001 — plugin contract: never raise
        return _dumps({"error": str(exc)})


def source_ledger_list(args: dict[str, Any], **kwargs: Any) -> str:
    """List recorded sources, optionally filtered by query."""
    del kwargs
    try:
        query = str(args.get("query") or "")
        return _dumps(ledger.list_sources(query=query))
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def source_ledger_cite(args: dict[str, Any], **kwargs: Any) -> str:
    """Format recorded sources. Do not invent citations outside this result."""
    del kwargs
    try:
        ids_raw = args.get("ids")
        ids: list[int] | None = None
        if isinstance(ids_raw, list):
            parsed: list[int] = []
            for item in ids_raw:
                try:
                    parsed.append(int(item))
                except (TypeError, ValueError):
                    return _dumps({"error": f"invalid ledger id: {item!r}"})
            ids = parsed
        style = str(args.get("style") or runtime.citation_style()).strip().lower()
        if style not in {"apa", "ieee", "chicago"}:
            style = runtime.citation_style()
        return _dumps(ledger.cite_sources(ids, style))
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def source_ledger_check(args: dict[str, Any], **kwargs: Any) -> str:
    """Compare a claim against the ledger. Unsourced claims stay unsourced."""
    del kwargs
    try:
        claim = str(args.get("claim") or "").strip()
        if not claim:
            return _dumps({"error": "claim is required"})
        return _dumps(ledger.check_claim(claim))
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})
