"""Policy fence. Fail closed when the rule cannot be evaluated."""

from __future__ import annotations

from typing import Any

from ..runtime import (
    FORBIDDEN_CROSS_IDS,
    OUROBOROS_PLUGIN_NAMES,
    RESERVED_PROFILE_NAMES,
    SECRET_FILENAMES,
    WRITE_TOOLS,
)
from ..store import ledger

_NAME_KEYS = ("name", "profile", "profile_name")


def _block(message: str) -> dict[str, str]:
    return {"action": "block", "message": message}


def _params(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any]]:
    tool_name = str(
        kwargs.get("tool_name")
        or kwargs.get("name")
        or (args[0] if args else "")
        or ""
    )
    params = kwargs.get("params") or kwargs.get("arguments") or kwargs.get("args")
    if params is None and len(args) >= 2 and isinstance(args[1], dict):
        params = args[1]
    if not isinstance(params, dict):
        params = {}
    return tool_name, params


def pre_tool_call(*args: Any, **kwargs: Any) -> Any:
    try:
        data = ledger.load_store()
        gov = data.get("governor") if isinstance(data.get("governor"), dict) else {}
        tool_name, params = _params(*args, **kwargs)
        if gov.get("state") == "HARD" and tool_name in {"docs_resolve", "docs_ask", "scaffold_profile"}:
            return _block("governor HARD: factory writes are closed for this run")
        if tool_name == "scaffold_profile":
            name = str(params.get("name") or "").strip()
            if not name:
                return _block("scaffold_profile requires name")
            lowered = name.lower()
            if lowered in RESERVED_PROFILE_NAMES:
                return _block(f"reserved profile name: {name}")
            if lowered in OUROBOROS_PLUGIN_NAMES:
                return _block(f"ouroboros plugin-name collision: {name}")
            if lowered in FORBIDDEN_CROSS_IDS:
                return _block(f"forbidden cross-profile id: {name}")
        if tool_name in WRITE_TOOLS:
            path = str(params.get("path") or params.get("file") or "")
            leaf = path.rsplit("/", 1)[-1]
            if leaf in SECRET_FILENAMES:
                return _block(f"refusing to write secret-shaped file {leaf}")
        return None
    except Exception as exc:  # noqa: BLE001
        return _block(f"fence could not evaluate: {exc}")
