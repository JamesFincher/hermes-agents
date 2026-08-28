"""Policy fence. Fail closed when the rule cannot be evaluated."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..runtime import (
    FORBIDDEN_CROSS_IDS,
    OUROBOROS_PLUGIN_NAMES,
    RESERVED_PROFILE_NAMES,
    SECRET_FILENAMES,
    WRITE_TOOLS,
    agent_name_from_path,
    find_repo_root,
)
from ..store import ledger
from ..store import plan as plan_store


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


def _plan_targets(tool_name: str, params: dict[str, Any]) -> list[str]:
    names: list[str] = []
    if tool_name == "scaffold_profile":
        raw = str(params.get("name") or "").strip().lower()
        if raw:
            names.append(raw)
    if tool_name in WRITE_TOOLS:
        path = str(params.get("path") or params.get("file") or "")
        target = agent_name_from_path(path)
        if target:
            names.append(target)
    unique: list[str] = []
    for item in names:
        if item not in unique:
            unique.append(item)
    return unique


def _canvas_missing(name: str) -> bool:
    current = plan_store.get_plan(name)
    stored = str((current or {}).get("canvas_path") or "")
    if stored and Path(stored).is_file():
        return False
    root = find_repo_root()
    if root is None:
        return True
    return not (root / "docs" / "profiles" / f"{name}-canvas.md").is_file()


def pre_tool_call(*args: Any, **kwargs: Any) -> Any:
    try:
        data = ledger.load_store()
        gov = data.get("governor") if isinstance(data.get("governor"), dict) else {}
        tool_name, params = _params(*args, **kwargs)
        if gov.get("state") == "HARD" and tool_name in {
            "docs_resolve",
            "docs_ask",
            "scaffold_profile",
            "write_canvas",
            "write_spec",
        }:
            return _block("governor HARD: factory writes are closed for this run")
        if tool_name == "investigate_surface":
            name = str(params.get("name") or "").strip().lower()
            if not name:
                return _block("investigate_surface requires name")
            current = plan_store.get_plan(name)
            if current is None or not current.get("started"):
                return _block("plan_start was not called for this name")
        if tool_name == "write_spec":
            name = str(params.get("name") or "").strip().lower()
            if not name:
                return _block("write_spec requires name")
            if _canvas_missing(name):
                return _block("write_spec fails until the canvas exists")
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
        if tool_name in WRITE_TOOLS or tool_name == "scaffold_profile":
            for target in _plan_targets(tool_name, params):
                if target == "inception":
                    continue
                if target in RESERVED_PROFILE_NAMES:
                    return _block(f"reserved profile name: {target}")
                if target in OUROBOROS_PLUGIN_NAMES:
                    return _block(f"ouroboros plugin-name collision: {target}")
                if target in FORBIDDEN_CROSS_IDS:
                    return _block(f"forbidden cross-profile id: {target}")
                result = plan_store.evaluate_plan(target)
                if not result.get("ok"):
                    first = (result.get("gaps") or ["plan incomplete"])[0]
                    return _block(f"check_plan is not ok for {target}: {first}")
        if tool_name in WRITE_TOOLS:
            path = str(params.get("path") or params.get("file") or "")
            leaf = path.rsplit("/", 1)[-1]
            if leaf in SECRET_FILENAMES:
                return _block(f"refusing to write secret-shaped file {leaf}")
        return None
    except Exception as exc:  # noqa: BLE001
        return _block(f"fence could not evaluate: {exc}")
