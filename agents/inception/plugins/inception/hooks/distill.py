"""Intercept-and-distil. Huge docs payloads become a card plus a pointer."""

from __future__ import annotations

import json
from typing import Any

from ..runtime import DOCS_TOOLS
from ..store import ledger

CARD_LIMIT = 900


def transform_tool_result(*args: Any, **kwargs: Any) -> Any:
    try:
        tool_name = str(
            kwargs.get("tool_name")
            or kwargs.get("name")
            or (args[0] if args else "")
            or ""
        )
        result = kwargs.get("result")
        if result is None and len(args) >= 2:
            result = args[1]
        if tool_name not in DOCS_TOOLS:
            return None
        if not isinstance(result, str) or len(result) <= CARD_LIMIT:
            return None
        try:
            payload = json.loads(result)
        except json.JSONDecodeError:
            payload = {"raw": result[:CARD_LIMIT]}
        if not isinstance(payload, dict):
            payload = {"raw": str(payload)[:CARD_LIMIT]}
        card_id = str((payload.get("card_id") or payload.get("stored_id") or ""))
        url = str(payload.get("openable_url") or "")
        summary = json.dumps(
            {
                "distilled": True,
                "tool": tool_name,
                "ok": payload.get("ok"),
                "error": payload.get("error"),
                "openable_url": url or None,
                "card_id": card_id or None,
                "pointer": f"plugin-data/inception/factory.json#cards/{card_id or 'none'}",
            },
            ensure_ascii=False,
        )
        if card_id:
            ledger.add_audit("distil", f"{tool_name} -> {card_id}")
        return summary
    except Exception:
        return None
