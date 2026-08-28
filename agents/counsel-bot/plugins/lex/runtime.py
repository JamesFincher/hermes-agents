"""Closed-over host context. Nothing else in the plugin imports Hermes."""
from __future__ import annotations
import os, threading
from pathlib import Path

_ctx = None
_settings: dict = {}
_lock = threading.RLock()


def bind(ctx) -> None:
    global _ctx, _settings
    with _lock:
        _ctx = ctx
        try:
            _settings = dict(getattr(ctx, "settings", {}) or {})
        except Exception:
            _settings = {}


def setting(key: str, default=None):
    return _settings.get(key, default)


def call_mcp(server: str, tool: str, args: dict) -> dict:
    """Returns {ok, result} or {ok: False, error}. Never raises."""
    if _ctx is None:
        return {"ok": False, "error": "plugin context not bound"}
    try:
        return _ctx.call_mcp(server, tool, args) or {"ok": False, "error": "empty envelope"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def data_dir() -> Path:
    """Durable, outside the install tree, survives compaction and profile update."""
    p = None
    if _ctx is not None:
        p = getattr(_ctx, "plugin_data_dir", None)
    if not p:
        home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
        p = Path(home) / "plugin-data" / "lex"
    p = Path(p)
    for sub in ("corpus", "matters", "audit", "index"):
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p
