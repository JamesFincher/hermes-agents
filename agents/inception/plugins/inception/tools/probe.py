"""Record official vs invented knobs before config is written."""

from __future__ import annotations

from typing import Any

from ..runtime import dump, error
from ..store import ledger
from ..store import plan as plan_store

_DECISIONS = frozenset({"accept", "reject", "default"})
_TAGS = frozenset({"DOC", "INF", "UNV"})


def probe_knob(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        knob = str(payload.get("knob") or "").strip()
        decision = str(payload.get("decision") or "").strip()
        tag = str(payload.get("tag") or "").strip().upper()
        reason = str(payload.get("reason") or "").strip()
        url = str(payload.get("url") or "").strip()
        code_depends = bool(payload.get("code_depends") or False)
        plan_name = str(payload.get("name") or "").strip().lower()
        if not knob or not decision or not tag or not reason:
            return error("knob, decision, tag, and reason are required")
        if decision not in _DECISIONS:
            return error("decision must be accept, reject, or default")
        if tag not in _TAGS:
            return error("tag must be DOC, INF, or UNV")
        if tag == "DOC" and not url.startswith("https://"):
            return error("[DOC] requires an official https URL")
        if tag == "UNV" and code_depends:
            return error("code must not depend on [UNV]")
        row = ledger.add_probe(
            {
                "knob": knob,
                "decision": decision,
                "tag": tag,
                "url": url,
                "reason": reason,
                "code_depends": code_depends,
                "plan": plan_name,
            }
        )
        if plan_name:
            plan_store.attach_knob(plan_name, row)
        return dump({"ok": True, "probe": row})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
