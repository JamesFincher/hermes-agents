"""Profile-scoped plugin runtime: ctx, settings, plugin-data root.

Official homes:
- settings: plugins.entries.<id>.settings via ctx.get_config
  https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- durable state: <HERMES_HOME>/plugin-data/<name>/
  (plugin_data_dir from plugins.plugin_storage; never the install tree)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

PLUGIN_ID = "research-bot"

_ctx: Any = None


def set_ctx(ctx: Any) -> None:
    global _ctx
    _ctx = ctx


def get_ctx() -> Any:
    return _ctx


def get_setting(key: str, default: Any) -> Any:
    ctx = _ctx
    if ctx is None:
        return default
    try:
        value = ctx.get_config(key, default=default)
    except Exception:
        return default
    return default if value is None else value


def citation_style() -> str:
    raw = str(get_setting("citation_style", "apa")).strip().lower()
    if raw in {"apa", "ieee", "chicago"}:
        return raw
    return "apa"


def strictness() -> str:
    raw = str(get_setting("strictness", "strict")).strip().lower()
    if raw in {"strict", "relaxed"}:
        return raw
    return "strict"


def plugin_data_root() -> Path:
    """Writable profile-scoped data. Never the plugin install directory."""
    try:
        from plugins.plugin_storage import plugin_data_dir

        return plugin_data_dir(PLUGIN_ID)
    except Exception:
        hermes_home = os.environ.get("HERMES_HOME")
        if hermes_home:
            root = Path(hermes_home) / "plugin-data" / PLUGIN_ID
        else:
            root = Path.home() / ".hermes" / "plugin-data" / PLUGIN_ID
        root.mkdir(parents=True, exist_ok=True)
        return root


def session_state_get(key: str, default: Any = None) -> Any:
    ctx = _ctx
    if ctx is None:
        return default
    state = getattr(ctx, "state", None)
    if state is None:
        return default
    try:
        return state.get(key, default=default)
    except Exception:
        return default


def session_state_set(key: str, value: Any) -> None:
    ctx = _ctx
    if ctx is None:
        return
    state = getattr(ctx, "state", None)
    if state is None:
        return
    try:
        state.set(key, value)
    except Exception:
        return
