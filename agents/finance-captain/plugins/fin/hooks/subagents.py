"""Pullers fetch; the parent computes. Verify children actually created snapshots."""
from __future__ import annotations
import re
from ..store import entity as E, snapshot as S, audit

SNAP = re.compile(r"\bS\d{1,5}\b")


def subagent_start(child_subagent_id=None, child_goal=None, **kwargs):
    audit.write("delegation", {"event": "start", "child": child_subagent_id,
                               "goal": (child_goal or "")[:200]})


def subagent_stop(child_summary=None, child_status=None, duration_ms=0,
                  tool_call_history=None, **kwargs):
    ids = sorted(set(SNAP.findall(child_summary or "")))
    real = [i for i in ids if S.get(i)]
    ghosts = [i for i in ids if i not in real]
    audit.write("delegation", {"event": "stop", "status": child_status, "ms": duration_ms,
                               "snapshots": real, "claimed_missing": ghosts,
                               "tool_calls": len(tool_call_history or [])})
