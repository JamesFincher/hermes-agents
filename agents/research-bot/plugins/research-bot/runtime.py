"""Closed-over plugin context. No install-tree writes.

Official durable home is plugin_data_dir("research-bot") / ctx.state.
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

No host HTTP client. If one is ever needed, use
plugins.plugin_utils.lazy_singleton / SingletonSlot — do not hand-roll
a global _client. ctx._cli_ref is None in gateway, hermes chat -q, and
kanban workers; do not use it.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

try:
    from plugins.plugin_storage import plugin_data_dir as official_plugin_data_dir
except ImportError:
    official_plugin_data_dir = None

PLUGIN_ID = "research-bot"
TOOLSET = "research-bot"
MCP_SERVER = "context7"
MCP_RESOLVE_TOOL = "resolve-library-id"
MCP_QUERY_TOOL = "query-docs"
CITATION_STYLES = frozenset({"apa", "ieee", "chicago"})

_ctx: Any = None


def set_ctx(ctx: Any) -> None:
    global _ctx
    _ctx = ctx


def get_ctx() -> Any:
    return _ctx


def citation_style() -> str:
    ctx = _ctx
    getter = getattr(ctx, "get_config", None) if ctx is not None else None
    if callable(getter):
        try:
            candidate = str(getter("citation_style", "apa") or "apa").lower()
            if candidate in CITATION_STYLES:
                return candidate
        except Exception:
            pass
    return "apa"


def plugin_data_root() -> Path:
    official: Callable[..., Any] | None = official_plugin_data_dir
    if callable(official):
        try:
            raw = official(PLUGIN_ID)
            if raw:
                path = Path(str(raw))
                path.mkdir(parents=True, exist_ok=True)
                return path
        except Exception:
            pass
    ctx = _ctx
    if ctx is not None:
        getter = getattr(ctx, "get_plugin_data_dir", None)
        if callable(getter):
            try:
                raw = getter(PLUGIN_ID)
                if raw:
                    path = Path(str(raw))
                    path.mkdir(parents=True, exist_ok=True)
                    return path
            except Exception:
                pass
        attr = getattr(ctx, "plugin_data_dir", None)
        if callable(attr):
            try:
                raw = attr(PLUGIN_ID)
                if raw:
                    path = Path(str(raw))
                    path.mkdir(parents=True, exist_ok=True)
                    return path
            except Exception:
                pass
        if attr:
            path = Path(str(attr))
            path.mkdir(parents=True, exist_ok=True)
            return path
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        path = Path(env_home) / "plugin-data" / PLUGIN_ID
        path.mkdir(parents=True, exist_ok=True)
        return path
    fallback = Path.home() / ".hermes" / "plugin-data" / PLUGIN_ID
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def session_id() -> str:
    ctx = _ctx
    sid = getattr(ctx, "session_id", None) if ctx is not None else None
    if sid:
        return str(sid)
    return "default"


def state_get(key: str, default: Any = None) -> Any:
    ctx = _ctx
    state = getattr(ctx, "state", None) if ctx is not None else None
    getter = getattr(state, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except Exception:
            return default
    return default


def state_set(key: str, value: Any) -> None:
    ctx = _ctx
    state = getattr(ctx, "state", None) if ctx is not None else None
    setter = getattr(state, "set", None)
    if callable(setter):
        try:
            setter(key, value)
        except Exception:
            return


def call_mcp(tool: str, arguments: dict[str, Any]) -> Any:
    ctx = _ctx
    caller = getattr(ctx, "call_mcp", None) if ctx is not None else None
    if not callable(caller):
        return {"ok": False, "error": "ctx.call_mcp is not available in this Hermes build"}
    try:
        return caller(MCP_SERVER, tool, arguments)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"call_mcp({MCP_SERVER}, {tool}) failed: {exc}"}
