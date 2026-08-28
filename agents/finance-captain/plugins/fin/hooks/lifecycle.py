from __future__ import annotations
import logging
from ..store import entity as E, snapshot as S, audit
from ..runtime import data_dir, setting

log = logging.getLogger("fin.lifecycle")


def on_session_start(session_id=None, model=None, platform=None, **kwargs):
    try:
        data_dir()
        e = E.load()
        if e:
            hours = int(setting("snapshot_staleness_hours", 24))
            stale = [s["id"] for s in S.index()["snapshots"]
                     if s["entity"] == e["entity_id"] and S.is_stale(s, hours)]
            if stale:
                audit.write("policy", {"event": "stale_snapshots_at_session_start",
                                       "count": len(stale)})
        log.info("fin session %s entity=%s", session_id, (e or {}).get("entity_id"))
    except Exception:
        log.exception("fin session init failed (non-fatal)")


def on_session_end(session_id=None, completed=None, interrupted=None, **kwargs):
    try:
        audit.write("policy", {"event": "session_end", "session": session_id,
                               "completed": completed, "interrupted": interrupted})
    except Exception:
        pass
