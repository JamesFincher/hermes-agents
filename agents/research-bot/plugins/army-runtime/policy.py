"""Optional product-code write policy for pre_tool_call.

Gated by plugins.entries.army-runtime.settings.write_policy.
Default off so the policy does not leak to agents that implement code.
Official directive: {"action": "block", "message": "..."}
https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .runtime import write_policy_mode

_WRITE_TOOLS = {"write_file", "patch"}
_CODE_SUFFIXES = {
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".swift",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".scala",
}
_RESEARCH_DIR_MARKERS = {
    "notes",
    "research",
    "briefs",
    "findings",
    "citations",
    "sources",
    "papers",
    "literature",
}
_RESEARCH_SUFFIXES = {".md", ".txt", ".bib", ".csv", ".json"}


def _target_path(args: dict[str, Any]) -> str:
    for key in ("path", "file", "filename", "target", "file_path"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def is_research_artifact(path: str) -> bool:
    if not path:
        return False
    parsed = Path(path)
    parts = {part.lower() for part in parsed.parts}
    if parts & _RESEARCH_DIR_MARKERS:
        return True
    return parsed.suffix.lower() in _RESEARCH_SUFFIXES


def is_product_code_path(path: str) -> bool:
    if not path:
        return False
    if is_research_artifact(path):
        return False
    return Path(path).suffix.lower() in _CODE_SUFFIXES


def write_policy(tool_name: str, args: dict[str, Any]) -> dict[str, str] | None:
    if tool_name not in _WRITE_TOOLS:
        return None
    if write_policy_mode() != "research":
        return None
    path = _target_path(args)
    if not is_product_code_path(path):
        return None
    return {
        "action": "block",
        "message": (
            f"army-runtime write_policy=research blocks product-code writes "
            f"({tool_name} → {path}). Write cited findings under notes/, "
            "research/, briefs/, findings/, or a .md/.txt/.bib artifact."
        ),
    }
