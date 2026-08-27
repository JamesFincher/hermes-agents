"""Evidence Bus: transform_tool_result. Fail open. Card, not the page."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from ..runtime import estimate_tokens, first_openable_url, setting
from ..store import bus, extract, ledger, run, sanitize, score, spans

# docs_query and scholar_search stay off this list. Those tools write cards
# themselves. Storing their JSON envelopes would fence out a later extract.
INTAKE_TOOLS = frozenset({"web_extract", "web_search", "browser_snapshot", "x_search"})
_STATUS_WORDS = {
    "paywall": "paywall",
    "subscribe to continue": "paywall",
    "forbidden": "403",
    "too many requests": "429",
    "rate limit": "429",
}


def _as_text(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False)
    except TypeError:
        return str(result)


def _coerce_result(result: Any) -> Any:
    if not isinstance(result, str):
        return result
    stripped = result.strip()
    if not stripped or stripped[0] not in "{[":
        return result
    try:
        loaded = json.loads(stripped)
    except json.JSONDecodeError:
        return result
    if isinstance(loaded, dict):
        return loaded
    if isinstance(loaded, list):
        hits = [item for item in loaded if isinstance(item, dict)]
        if hits:
            return {"results": hits}
    return result


def _parse_result(tool_name: str, result: Any) -> tuple[str, str, list[dict[str, Any]], Any]:
    parsed = _coerce_result(result)
    text = _as_text(parsed if isinstance(parsed, dict) else result)
    url = ""
    extras: list[dict[str, Any]] = []
    if isinstance(parsed, dict):
        url = str(
            parsed.get("url")
            or parsed.get("canonical")
            or parsed.get("source")
            or parsed.get("link")
            or ""
        )
        for key in ("content", "text", "markdown", "html"):
            if key in parsed and isinstance(parsed[key], str):
                text = parsed[key]
                break
        hits = parsed.get("results") or parsed.get("organic") or parsed.get("items")
        if isinstance(hits, list):
            for hit in hits[:12]:
                if isinstance(hit, dict):
                    extras.append(hit)
    if not url:
        url = first_openable_url(text)
    del tool_name
    return url, text, extras, parsed


def detect_fetch_status(parsed: Any, text: str) -> str:
    if isinstance(parsed, dict):
        explicit = parsed.get("fetch_status")
        if explicit in {"ok", "paywall", "403", "429", "archived", "pdf-ocr"}:
            return str(explicit)
        status = parsed.get("status") or parsed.get("status_code") or parsed.get("code")
        try:
            code = int(status)
        except (TypeError, ValueError):
            code = None
        if code == 403:
            return "403"
        if code == 429:
            return "429"
        if code in {401, 402} or parsed.get("paywall") is True:
            return "paywall"
        err = str(parsed.get("error") or parsed.get("message") or "").lower()
        if "paywall" in err:
            return "paywall"
        if "403" in err or "forbidden" in err:
            return "403"
        if "429" in err or "rate limit" in err:
            return "429"
    blob = (text or "").lower()
    for needle, status in _STATUS_WORDS.items():
        if needle in blob:
            return status
    if not (text or "").strip():
        return "empty"
    return "ok"


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
        "fetch_status": source.get("fetch_status") or "ok",
    }


def _dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _fit_card(card: dict[str, Any]) -> str:
    payload = _dump_json({"ok": True, **card})
    if estimate_tokens(payload) <= 400:
        return payload
    slim = dict(card)
    slim["spans"] = list(slim.get("spans") or [])[:1]
    payload = _dump_json({"ok": True, **slim})
    if estimate_tokens(payload) <= 400:
        return payload
    slim["spans"] = []
    slim["title"] = ""
    payload = _dump_json({"ok": True, **slim})
    if estimate_tokens(payload) <= 400:
        return payload
    stub = {
        "ok": True,
        "card": card.get("card"),
        "canonical": card.get("canonical"),
        "read_more": card.get("read_more"),
        "untrusted": True,
        "note": "card trimmed",
    }
    return _dump_json(stub)


def _fit_cards(cards: list[dict[str, Any]]) -> str:
    note = "search hits; extract to fill corpus"
    kept = list(cards)
    payload = _dump_json({"ok": True, "cards": kept, "note": note})
    while estimate_tokens(payload) > 400 and kept:
        kept = kept[:-1]
        payload = _dump_json({"ok": True, "cards": kept, "note": note, "trimmed": True})
    if estimate_tokens(payload) > 400:
        return _dump_json({"ok": True, "cards": [], "note": note, "trimmed": True})
    return payload


def _audit(
    current: dict[str, Any] | None,
    *,
    tool: str,
    tokens_in: int,
    tokens_out: int,
    blocked: bool,
    reason: str,
) -> None:
    bus.append_audit(
        (current or {}).get("run_id") or "",
        {
            "tool": tool,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "blocked": blocked,
            "reason": reason,
        },
    )


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
        tokens_in = estimate_tokens(_as_text(result))
        url, text, extras, parsed = _parse_result(tool_name, result)
        current = run.load_run()
        cards: list[dict[str, Any]] = []
        if extras and tool_name in {"web_search", "x_search"}:
            for hit in extras:
                hit_url = str(hit.get("url") or hit.get("link") or hit.get("href") or "")
                if not hit_url:
                    continue
                canonical = bus.canonicalize(hit_url)
                snippet = str(hit.get("snippet") or hit.get("content") or "")[:400]
                cleaned = sanitize.strip_injections(snippet)
                if cleaned.get("suppressed"):
                    bus.append_audit(
                        (current or {}).get("run_id") or "",
                        {"suppressed": cleaned["suppressed"], "url": hit_url},
                    )
                added = ledger.add_source(
                    {
                        "url": hit_url,
                        "canonical_url": canonical,
                        "title": hit.get("title") or hit_url,
                        "quote": str(cleaned.get("text") or "")[:400],
                        "origin": tool_name,
                        "run_id": (current or {}).get("run_id") or "",
                        "needs_backfill": True,
                    }
                )
                source = added.get("source") or {}
                cards.append(_card_for_source(source, "", 0))
                host = (urlparse(hit_url).hostname or "").lower()
                if host:
                    run.bump_domain(host)
            payload = _fit_cards(cards)
            _note_batch(current, [c.get("card") for c in cards if c.get("card")])
            _audit(
                current,
                tool=tool_name,
                tokens_in=tokens_in,
                tokens_out=estimate_tokens(payload),
                blocked=False,
                reason="search-cards",
            )
            return payload
        if not url and not text:
            return None
        if not url:
            url = str((args or {}).get("url") or (args or {}).get("query") or "urn:hdr:inline")
        fetch_status = detect_fetch_status(parsed, text)
        if setting("untrusted_content_wrapping", True):
            scanned = sanitize.scan(text)
            if scanned.get("suppressed"):
                bus.append_audit(
                    (current or {}).get("run_id") or "",
                    {"suppressed": scanned["suppressed"], "url": url},
                )
        meta = extract.extract_metadata(text, url)
        scored = score.score_source(bus.canonicalize(url) or url, meta)
        stored: dict[str, Any] = {}
        selected: list[dict[str, Any]] = []
        useful = bool(text.strip()) and fetch_status != "empty"
        created_corpus = False
        if useful:
            stored = bus.write_corpus(
                text,
                {"url": url, "canonical": bus.canonicalize(url), "title": meta.get("title") or ""},
            )
            created_corpus = bool(stored.get("created"))
            selected = spans.select_spans(text, (current or {}).get("question") or "")
        added = ledger.add_source(
            {
                "url": url,
                "canonical_url": bus.canonicalize(url),
                "title": meta.get("title") or url,
                "authors": meta.get("authors") or [],
                "publisher": meta.get("publisher") or "",
                "container": meta.get("container") or "",
                "published": meta.get("published"),
                "doi": meta.get("doi"),
                "arxiv": meta.get("arxiv"),
                "kind": scored["kind"],
                "tier": scored["tier"],
                "tier_reason": scored["tier_reason"],
                "corpus": stored.get("path"),
                "bytes": stored.get("bytes"),
                "content_hash": f"sha256:{stored.get('sha256')}" if stored.get("sha256") else None,
                "spans": selected,
                "origin": tool_name,
                "quote": selected[0]["q"] if selected else "",
                "run_id": (current or {}).get("run_id") or "",
                "needs_backfill": not useful,
                "fetch_status": fetch_status,
            }
        )
        source = added.get("source") or {}
        nbytes = int(stored.get("bytes") or source.get("bytes") or 0)
        run.note_retrieval(
            created_corpus=created_corpus,
            new_row=not bool(added.get("updated")),
            nbytes=nbytes,
            filled_bytes=bool(added.get("updated") and created_corpus),
            reason="intake_corpus",
        )
        card = _card_for_source(source, str(stored.get("path") or ""), int(stored.get("chars") or 0))
        payload = _fit_card(card)
        bus.append_audit(
            (current or {}).get("run_id") or "",
            {
                "event": "card_economics",
                "page_chars": int(stored.get("chars") or 0),
                "card_tokens": estimate_tokens(payload),
            },
        )
        _note_batch(current, [source.get("id")])
        if url:
            host = (urlparse(url).hostname or "").lower()
            if host:
                run.bump_domain(host)
        _audit(
            current,
            tool=tool_name,
            tokens_in=tokens_in,
            tokens_out=estimate_tokens(payload),
            blocked=False,
            reason="card",
        )
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
    run.append_last_batch(ids)
    if not current:
        return
    batch = list(current.get("last_batch_ids") or [])
    for item in ids:
        if item and str(item) not in batch:
            batch.append(str(item))
    current["last_batch_ids"] = batch


