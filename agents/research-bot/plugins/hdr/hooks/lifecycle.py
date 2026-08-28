"""Session start/end. Init store, migrate, prune, archive."""

from __future__ import annotations

from typing import Any

from ..runtime import setting
from ..store import bus, index as inverted, ledger, run


def on_session_start(session_id: str = "", model: str = "", platform: str = "", **kwargs: Any) -> None:
    del session_id, model, platform, kwargs
    try:
        ledger.init_ledger()
        days = int(setting("corpus_retention_days", 30) or 30)
        data = ledger.load_ledger()
        removed = bus.prune_corpus(days)
        for digest in removed:
            archived = _archive_for_digest(data, digest)
            ledger.mark_corpus_gone(digest, archived_url=archived)
        inverted.rebuild()
    except Exception:
        return


def _archive_for_digest(data: dict[str, Any], digest: str) -> str:
    needle = bus.hash_key(digest)
    for source in data.get("sources") or []:
        if not isinstance(source, dict):
            continue
        corpus = str(source.get("corpus") or "")
        hashed = bus.hash_key(source.get("content_hash"))
        if needle not in corpus and hashed != needle:
            continue
        existing = str(source.get("archived_url") or "").strip()
        if existing:
            return existing
        url = str(source.get("canonical_url") or source.get("url") or "").strip()
        wayback = bus.wayback_latest_url(url)
        if wayback:
            return wayback
    return f"file://gone/{digest}"


def on_session_end(session_id: str = "", **kwargs: Any) -> None:
    del session_id, kwargs
    try:
        current = run.load_run()
        if current:
            run.archive_run(current)
            bus.append_audit(current.get("run_id") or "", {"event": "session_end"})
    except Exception:
        return


def on_session_finalize(session_id: str = "", **kwargs: Any) -> None:
    on_session_end(session_id, **kwargs)


def on_session_reset(session_id: str = "", **kwargs: Any) -> None:
    on_session_end(session_id, **kwargs)
    try:
        run.clear_run()
        ledger.init_ledger()
    except Exception:
        return


def api_request_error(error: str = "", **kwargs: Any) -> None:
    try:
        current = run.load_run()
        kind = _classify_api_error(error, kwargs)
        bus.append_audit(
            (current or {}).get("run_id") or "",
            {
                "event": "api_request_error",
                "class": kind,
                "error": str(error),
                "detail": str(kwargs)[:400],
            },
        )
    except Exception:
        return


def _classify_api_error(error: str, extra: dict[str, Any]) -> str:
    blob = f"{error} {extra}".lower()
    if any(token in blob for token in ("429", "rate limit", "rate_limit", "too many requests")):
        return "rate_limit"
    if any(
        token in blob
        for token in ("401", "403", "unauthorized", "forbidden", "invalid api key", "auth")
    ):
        return "auth"
    if any(token in blob for token in ("timeout", "timed out", "deadline exceeded")):
        return "timeout"
    if any(
        token in blob
        for token in ("context length", "context_length", "too many tokens", "maximum context")
    ):
        return "context"
    return "other"
