from __future__ import annotations
import logging
from ..store import bus, ledger as L, matter as M
from ..runtime import setting, data_dir

log = logging.getLogger("lex.lifecycle")


def on_session_start(session_id=None, model=None, platform=None, **kwargs):
    try:
        data_dir()
        L.save(L.load())                       # forces schema migration on load
        days = int(setting("corpus_retention_days", 90) or 90)
        n = bus.prune(days)
        m = M.load()
        log.info("lex session %s: matter=%s pruned=%d", session_id,
                 (m or {}).get("matter_id"), n)
    except Exception:
        log.exception("lex session init failed (non-fatal)")


def on_session_end(session_id=None, completed=None, interrupted=None, **kwargs):
    try:
        m = M.load()
        if m:
            M.save(m)
    except Exception:
        pass
