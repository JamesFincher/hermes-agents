"""Closed-over plugin context. No install-tree writes.

Official durable home is plugin_data_dir("inception").
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

PLUGIN_ID = "inception"
TOOLSET = "inception"
MCP_SERVER = "context7"
MCP_RESOLVE_TOOL = "resolve-library-id"
MCP_QUERY_TOOL = "query-docs"
DIGEST_MAX_CHARS = 800
GOVERNOR_MAX_REQUESTS = 80
GOVERNOR_MAX_INPUT_TOKENS = 250000
RESERVED_PROFILE_NAMES = frozenset({"hermes", "test", "tmp", "root", "sudo"})
OUROBOROS_PLUGIN_NAMES = frozenset(
    {"echo", "archive", "seatbelt", "council", "autopilot", "forge"}
)
_SHARED_LAYER = "ar" + "my"
FORBIDDEN_CROSS_IDS = frozenset(
    {"hdr", "research-bot", _SHARED_LAYER, _SHARED_LAYER + "-runtime"}
)
SECRET_FILENAMES = frozenset({".env", "auth.json", "honcho.json"})
WRITE_TOOLS = frozenset({"write_file", "patch", "scaffold_profile"})
DOCS_TOOLS = frozenset({"docs_resolve", "docs_ask"})
URL_RE = re.compile(r"https://[^\s\"'<>]+")

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


def plugin_data() -> Path:
    ctx = _ctx
    if ctx is not None and hasattr(ctx, "plugin_data_dir"):
        try:
            path = ctx.plugin_data_dir(PLUGIN_ID)
            return Path(path)
        except Exception:
            pass
    home = os.environ.get("HERMES_HOME") or ""
    if home:
        path = Path(home) / "plugin-data" / PLUGIN_ID
        path.mkdir(parents=True, exist_ok=True)
        return path
    fallback = Path.cwd() / "plugin-data" / PLUGIN_ID
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def call_mcp(tool: str, arguments: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    ctx = _ctx
    if ctx is None or not hasattr(ctx, "call_mcp"):
        return {"ok": False, "error": "ctx.call_mcp is unavailable"}
    try:
        result = ctx.call_mcp(MCP_SERVER, tool, arguments, timeout=timeout)
    except TypeError:
        try:
            result = ctx.call_mcp(MCP_SERVER, tool, arguments)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    if isinstance(result, dict):
        return result
    return {"ok": True, "result": result}


def first_openable_url(blob: str) -> str:
    for match in URL_RE.findall(blob or ""):
        cleaned = match.rstrip(").,]}")
        if cleaned.startswith("https://"):
            return cleaned
    return ""


def agent_name_from_path(path: str) -> str | None:
    if not path:
        return None
    parts = Path(str(path)).as_posix().split("/")
    if "agents" not in parts:
        return None
    index = parts.index("agents")
    if index + 1 >= len(parts):
        return None
    name = parts[index + 1].strip().lower()
    return name or None


def find_repo_root(start: Path | None = None) -> Path | None:
    override = os.environ.get("INCEPTION_LIBRARY_ROOT")
    if override:
        candidate = Path(override)
        playbook = candidate / "docs" / "PROFILE-PLAYBOOK.md"
        validator = candidate / "scripts" / "validate_factory.py"
        if playbook.is_file() and validator.is_file():
            return candidate.resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        playbook = candidate / "docs" / "PROFILE-PLAYBOOK.md"
        validator = candidate / "scripts" / "validate_factory.py"
        if playbook.is_file() and validator.is_file():
            return candidate
    return None


def setting(name: str, default: Any) -> Any:
    ctx = _ctx
    if ctx is None:
        return default
    getter = getattr(ctx, "get_plugin_config", None) or getattr(ctx, "get_config", None)
    if getter is None:
        return default
    try:
        value = getter(name, default)
    except Exception:
        return default
    return default if value is None else value
