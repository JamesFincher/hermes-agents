"""Closed-over plugin context. No install-tree writes.

Official durable home is plugin_data_dir("hdr") / ctx.state.
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from plugins.plugin_storage import plugin_data_dir as official_plugin_data_dir
except ImportError:
    official_plugin_data_dir = None

PLUGIN_ID = "hdr"
TOOLSET = "hdr"
MCP_SERVER = "context7"
MCP_RESOLVE_TOOL = "resolve-library-id"
MCP_QUERY_TOOL = "query-docs"
CITATION_STYLES = frozenset({"apa", "ieee", "chicago"})
TIERS = frozenset({"quick", "standard", "deep", "exhaustive"})
BRIEF_DIRS = frozenset(
    {"notes", "research", "briefs", "findings", "citations", "sources", "data"}
)
# Citation Gate applies to brief-class paths only. Analysis artifacts stay writable.
CITATION_GATE_DIRS = frozenset({"briefs", "research", "findings"})
INTERCEPTED = frozenset({"todo", "memory", "session_search", "delegate_task"})
NETWORK_TOOLS = frozenset(
    {
        "web_search",
        "web_extract",
        "browser_navigate",
        "browser_snapshot",
        "x_search",
        "docs_query",
        "resolve_library",
        "scholar_search",
        "archive_lookup",
    }
)
WRITE_TOOLS = frozenset({"write_file", "patch"})
TERMINAL_TOOLS = frozenset({"terminal", "execute_code"})
# RED blocks fetch tools and shell/code egress. Fetch counter stays on NETWORK_TOOLS.
RED_EGRESS_TOOLS = NETWORK_TOOLS | TERMINAL_TOOLS
READ_ONLY_WHEN_HARD = frozenset(
    {
        "read_file",
        "evidence_read",
        "evidence_search",
        "evidence_stats",
        "gap_scan",
        "claim_verify",
        "conflict_report",
        "cite_source",
        "research_plan",
        "worker_harvest",
        "write_file",
        "patch",
    }
)

DOMAIN_SOFT_CAP = 4

TIER_BUDGET = {
    "quick": {"tokens": 40_000, "fetches": 5, "seconds": 90, "workers": 0},
    "standard": {"tokens": 200_000, "fetches": 25, "seconds": 360, "workers": 3},
    "deep": {"tokens": 800_000, "fetches": 80, "seconds": 1200, "workers": 6},
    "exhaustive": {"tokens": 3_000_000, "fetches": 250, "seconds": 3600, "workers": 10},
}

_ctx: Any = None


def set_ctx(ctx: Any) -> None:
    global _ctx
    _ctx = ctx


def get_ctx() -> Any:
    return _ctx


def dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def error(message: str) -> str:
    return dump({"error": message})


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


def setting(key: str, default: Any) -> Any:
    ctx = _ctx
    getter = getattr(ctx, "get_config", None) if ctx is not None else None
    if callable(getter):
        try:
            return getter(key, default)
        except Exception:
            return default
    return default


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
        for name in ("get_plugin_data_dir", "plugin_data_dir"):
            attr = getattr(ctx, name, None)
            if callable(attr):
                try:
                    raw = attr(PLUGIN_ID)
                    if raw:
                        path = Path(str(raw))
                        path.mkdir(parents=True, exist_ok=True)
                        return path
                except Exception:
                    pass
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        path = Path(env_home) / "plugin-data" / PLUGIN_ID
        path.mkdir(parents=True, exist_ok=True)
        return path
    fallback = Path.home() / ".hermes" / "plugin-data" / PLUGIN_ID
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


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


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def normalize_envelope(envelope: Any) -> dict[str, Any]:
    if isinstance(envelope, dict):
        if "ok" in envelope or "error" in envelope:
            return envelope
        return {"ok": True, "result": envelope}
    if isinstance(envelope, str):
        try:
            loaded = json.loads(envelope)
        except json.JSONDecodeError:
            return {"ok": True, "result": envelope}
        if isinstance(loaded, dict):
            return loaded
        return {"ok": True, "result": loaded}
    return {"ok": True, "result": envelope}


def first_openable_url(text: str) -> str:
    if not text:
        return ""
    for match in re.findall(r"https?://[^\s\"'<>]+", text):
        cleaned = match.rstrip(").,];")
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned
    return ""
