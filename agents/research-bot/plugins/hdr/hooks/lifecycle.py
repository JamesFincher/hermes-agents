"""Session start/end. Init store, migrate, prune, archive."""

from __future__ import annotations

from typing import Any

from ..runtime import setting
from ..store import bus, ledger, run


def on_session_start(session_id: str = "", model: str = "", platform: str = "", **kwargs: Any) -> None:
    del session_id, model, platform, kwargs
    try:
        ledger.init_ledger()
        days = int(setting("corpus_retention_days", 30) or 30)
        removed = bus.prune_corpus(days)
        for digest in removed:
            ledger.mark_corpus_gone(digest)
    except Exception:
        return


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
        ledger.init_ledger()
    except Exception:
        return


def api_request_error(error: str = "", **kwargs: Any) -> None:
    try:
        current = run.load_run()
        bus.append_audit(
            (current or {}).get("run_id") or "",
            {"event": "api_request_error", "error": str(error), "detail": str(kwargs)[:400]},
        )
    except Exception:
        return
