"""evidence_add / search / read / stats."""

from __future__ import annotations

from typing import Any

from ..runtime import dump, error
from ..store import bus, extract, ledger, run, score, spans


def evidence_add(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        url = str((args or {}).get("url") or "").strip()
        if not url:
            return error("url is required")
        text = str((args or {}).get("text") or "")
        current = run.load_run()
        canonical = bus.canonicalize(url)
        meta = extract.extract_metadata(text, url)
        if (args or {}).get("title"):
            meta["title"] = str(args["title"])
        scored = score.score_source(canonical or url, meta)
        corpus = None
        content_hash = None
        nbytes = 0
        selected = []
        if text:
            stored = bus.write_corpus(
                text,
                {"url": url, "canonical": canonical, "title": meta.get("title") or ""},
            )
            corpus = stored.get("path")
            content_hash = f"sha256:{stored.get('sha256')}"
            nbytes = int(stored.get("bytes") or 0)
            selected = spans.select_spans(text, (current or {}).get("question") or "")
        result = ledger.add_source(
            {
                "url": url,
                "canonical_url": canonical,
                "title": meta.get("title") or (args or {}).get("title") or "",
                "authors": meta.get("authors") or [],
                "publisher": meta.get("publisher") or "",
                "published": meta.get("published"),
                "doi": meta.get("doi"),
                "arxiv": meta.get("arxiv"),
                "kind": (args or {}).get("kind") or scored["kind"],
                "tier": scored["tier"],
                "tier_reason": scored["tier_reason"],
                "corpus": corpus,
                "bytes": nbytes,
                "content_hash": content_hash,
                "spans": selected,
                "origin": (args or {}).get("origin") or "manual",
                "quote": (args or {}).get("quote") or (selected[0]["q"] if selected else ""),
                "run_id": (current or {}).get("run_id") or "",
                "needs_backfill": not bool(text),
            }
        )
        return dump(result)
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def evidence_search(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        query = str((args or {}).get("query") or "")
        sources = ledger.list_sources(query=query)
        cards = []
        backfill = 0
        for source in sources[:25]:
            if source.get("needs_backfill"):
                backfill += 1
            cards.append(
                {
                    "id": source.get("id"),
                    "title": source.get("title"),
                    "url": source.get("canonical_url") or source.get("url"),
                    "tier": source.get("tier"),
                    "kind": source.get("kind"),
                    "spans": source.get("spans") or [],
                    "needs_backfill": bool(source.get("needs_backfill")),
                }
            )
        return dump({"ok": True, "count": len(cards), "backfill_needed": backfill, "cards": cards})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def evidence_read(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        src = str((args or {}).get("src") or "")
        source = ledger.get_source(src)
        if not source:
            return error(f"unknown source {src}")
        corpus = str(source.get("corpus") or "")
        if not corpus:
            return error(f"{src} has no corpus (needs_backfill or pruned)")
        digest = corpus.split("/")[-1].replace(".txt", "")
        offset = int((args or {}).get("offset") or 0)
        limit = int((args or {}).get("limit") or 4000)
        around = (args or {}).get("around_span")
        if around is not None and source.get("spans"):
            try:
                span = source["spans"][int(around)]
                offset = max(0, int(span.get("off") or 0) - 200)
            except Exception:
                pass
        return dump(bus.read_corpus(digest, offset=offset, limit=limit))
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def evidence_stats(args: dict[str, Any], **kwargs: Any) -> str:
    del args, kwargs
    try:
        current = run.load_run()
        sources = ledger.list_sources()
        by_tier: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        for source in sources:
            tier = str(source.get("tier") or "D")
            by_tier[tier] = by_tier.get(tier, 0) + 1
        return dump(
            {
                "ok": True,
                "sources": len(sources),
                "by_tier": by_tier,
                "open_questions": (current or {}).get("open_questions") or [],
                "new_source_yield": (current or {}).get("new_source_yield"),
                "governor": (current or {}).get("governor"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
