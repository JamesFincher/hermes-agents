"""Evidence Bus: transform_tool_result. Fail open. Card, not the page."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from ..runtime import estimate_tokens, first_openable_url
from ..store import bus, extract, ledger, run, sanitize, score, spans

INTAKE_TOOLS = frozenset(
    {"web_extract", "web_search", "docs_query", "browser_snapshot", "x_search"}
)


def _as_text(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False)
    except TypeError:
        return str(result)


def _parse_result(tool_name: str, result: Any) -> tuple[str, str, list[dict[str, Any]]]:
    text = _as_text(result)
    url = ""
    extras: list[dict[str, Any]] = []
    if isinstance(result, dict):
        url = str(
            result.get("url")
            or result.get("canonical")
            or result.get("source")
            or result.get("link")
            or ""
        )
        body = result.get("content") or result.get("text") or result.get("markdown") or result.get("html")
        if isinstance(body, str) and body.strip():
            text = body
        hits = result.get("results") or result.get("organic") or result.get("items")
        if isinstance(hits, list):
            for hit in hits[:12]:
                if isinstance(hit, dict):
                    extras.append(hit)
    if not url:
        url = first_openable_url(text)
    del tool_name
    return url, text, extras


def _card_for_source(source: dict[str, Any], corpus_path: str, chars: int) -> dict[str, Any]:
    return {
        "card": source.get("id"),
        "url": source.get("url"),
        "canonical": source.get("canonical_url"),
        "title": source.get("title"),
        "publisher": source.get("publisher"),
        "published": source.get("published"),
        "accessed": source.get("retrieved"),
        "kind": source.get("kind"),
        "tier": source.get("tier"),
        "spans": source.get("spans") or [],
        "full": f"{corpus_path} ({chars} chars)" if corpus_path else None,
        "read_more": f"evidence_read src={source.get('id')}" if corpus_path else None,
        "untrusted": True,
    }


def transform_tool_result(
    tool_name: str,
    result: Any,
    args: dict[str, Any] | None = None,
    **kwargs: Any,
) -> str | None:
    del kwargs
    try:
        if tool_name not in INTAKE_TOOLS:
            return None
        url, text, extras = _parse_result(tool_name, result)
        current = run.load_run()
        cards: list[dict[str, Any]] = []
        if extras and tool_name in {"web_search", "x_search"}:
            for hit in extras:
                hit_url = str(hit.get("url") or hit.get("link") or hit.get("href") or "")
                if not hit_url:
                    continue
                canonical = bus.canonicalize(hit_url)
                added = ledger.add_source(
                    {
                        "url": hit_url,
                        "canonical_url": canonical,
                        "title": hit.get("title") or hit_url,
                        "quote": str(hit.get("snippet") or hit.get("content") or "")[:400],
                        "origin": tool_name,
                        "run_id": (current or {}).get("run_id") or "",
                        "needs_backfill": True,
                    }
                )
                source = added.get("source") or {}
                cards.append(_card_for_source(source, "", 0))
            payload = json.dumps({"ok": True, "cards": cards, "note": "search hits; extract to fill corpus"}, ensure_ascii=False)
            if estimate_tokens(payload) > 400:
                payload = payload[:1600]
            _note_batch(current, [c.get("card") for c in cards if c.get("card")])
            return payload
        if not url and not text:
            return None
        if not url:
            url = str((args or {}).get("url") or (args or {}).get("query") or "urn:hdr:inline")
        wrapped = sanitize.wrap(text)
        meta = extract.extract_metadata(wrapped["text"], url)
        scored = score.score_source(bus.canonicalize(url) or url, meta)
        stored = bus.write_corpus(
            text,
            {"url": url, "canonical": bus.canonicalize(url), "title": meta.get("title") or ""},
        )
        selected = spans.select_spans(text, (current or {}).get("question") or "")
        added = ledger.add_source(
            {
                "url": url,
                "canonical_url": bus.canonicalize(url),
                "title": meta.get("title") or url,
                "authors": meta.get("authors") or [],
                "publisher": meta.get("publisher") or "",
                "published": meta.get("published"),
                "doi": meta.get("doi"),
                "arxiv": meta.get("arxiv"),
                "kind": scored["kind"],
                "tier": scored["tier"],
                "tier_reason": scored["tier_reason"],
                "corpus": stored.get("path"),
                "bytes": stored.get("bytes"),
                "content_hash": f"sha256:{stored.get('sha256')}",
                "spans": selected,
                "origin": tool_name,
                "quote": selected[0]["q"] if selected else "",
                "run_id": (current or {}).get("run_id") or "",
                "needs_backfill": False,
            }
        )
        source = added.get("source") or {}
        card = _card_for_source(source, str(stored.get("path") or ""), int(stored.get("chars") or 0))
        if wrapped.get("suppressed"):
            bus.append_audit((current or {}).get("run_id") or "", {"suppressed": wrapped["suppressed"], "url": url})
        payload = json.dumps({"ok": True, **card}, ensure_ascii=False)
        if estimate_tokens(payload) > 400:
            card["spans"] = card.get("spans")[:1]
            payload = json.dumps({"ok": True, **card}, ensure_ascii=False)
            if estimate_tokens(payload) > 400:
                payload = payload[:1600]
        _note_batch(current, [source.get("id")])
        if current and url:
            counts = current.setdefault("domain_counts", {})
            host = (urlparse(url).hostname or "").lower()
            if host:
                counts[host] = int(counts.get(host) or 0) + 1
                run.save_run(current)
        return payload
    except Exception:
        return None


def transform_terminal_output(output: str, **kwargs: Any) -> str | None:
    del kwargs
    try:
        text = output or ""
        if len(text) < 4000:
            return None
        lines = text.splitlines()
        head = "\n".join(lines[:40])
        urls = re.findall(r"https?://[^\s\"'<>]+", text)
        return (
            f"[HDR terminal collapse] {len(text)} chars, {len(lines)} lines, "
            f"{len(set(urls))} urls\n{head}\n…"
        )
    except Exception:
        return None


def _note_batch(current: dict[str, Any] | None, ids: list[Any]) -> None:
    if not current:
        return
    batch = list(current.get("last_batch_ids") or [])
    for item in ids:
        if item and str(item) not in batch:
            batch.append(str(item))
    current["last_batch_ids"] = batch
    run.save_run(current)
