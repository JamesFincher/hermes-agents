"""Reconcile delegated authority retrieval without paying for it twice.

Children write to the same plugin-data ledger. The parent harvests ids and
counts; raw opinion text never crosses the boundary.
"""
from __future__ import annotations
import json, logging, re
from ..store import matter as M, ledger as L
from ..runtime import data_dir

log = logging.getLogger("lex.subagents")
AUTH_RE = re.compile(r"\bA\d{1,5}\b")


def subagent_start(child_subagent_id=None, child_goal=None, **kwargs):
    try:
        m = M.load()
        if not m:
            return
        m.setdefault("delegations", []).append(
            {"child": child_subagent_id, "goal": (child_goal or "")[:300], "status": "running"})
        M.save(m)
    except Exception:
        pass


def subagent_stop(child_summary=None, child_status=None, duration_ms=0,
                  tool_call_history=None, **kwargs):
    try:
        m = M.load()
        if not m:
            return
        ids = sorted(set(AUTH_RE.findall(child_summary or "")))
        real = [i for i in ids if L.get(i)]
        ghosts = [i for i in ids if i not in real]
        for d in m.get("delegations", []):
            if d.get("status") == "running":
                d.update({"status": child_status, "ms": duration_ms,
                          "authorities": real, "claimed_but_missing": ghosts,
                          "tool_calls": len(tool_call_history or [])})
                break
        M.save(m)
        with (data_dir() / "audit" / "delegation.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"status": child_status, "ms": duration_ms,
                                "authorities": real, "ghosts": ghosts}, default=str) + "\n")
        if ghosts:
            log.warning("child reported authority ids not in the ledger: %s", ghosts)
    except Exception:
        pass
