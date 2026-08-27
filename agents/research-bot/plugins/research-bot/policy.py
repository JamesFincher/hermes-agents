"""Research write policy for pre_tool_call. This profile only."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_WRITE_TOOLS = frozenset({"write_file", "patch"})
_TERMINAL_TOOLS = frozenset({"terminal", "execute_code"})
_CODE_SUFFIXES = {
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".swift",
    ".c",
    ".cpp",
    ".cs",
}
_RESEARCH_DIRS = {
    "notes",
    "research",
    "briefs",
    "findings",
    "citations",
    "sources",
    "papers",
    "literature",
}
_RESEARCH_SUFFIXES = {".md", ".txt", ".bib", ".csv"}
_SCAFFOLD = re.compile(
    r"\b("
    r"npm\s+(init|create)|npx\s+create-|yarn\s+create|pnpm\s+create|"
    r"create-next-app|create-react-app|vite\s+create|"
    r"cargo\s+new|django-admin\s+startproject|rails\s+new|"
    r"poetry\s+new|git\s+init"
    r")\b",
    re.IGNORECASE,
)
# Agent-loop intercepts these BEFORE handle_function_call / registry.
# pre_tool_call never sees a real dispatch — do not police them.
# https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
_INTERCEPTED = frozenset({"todo", "memory", "session_search", "delegate_task"})


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
    if parts & _RESEARCH_DIRS:
        return True
    return parsed.suffix.lower() in _RESEARCH_SUFFIXES


def write_policy(tool_name: str, args: dict[str, Any]) -> dict[str, str] | None:
    if tool_name in _INTERCEPTED:
        return None
    if tool_name in _WRITE_TOOLS:
        path = _target_path(args)
        if is_research_artifact(path):
            return None
        if Path(path).suffix.lower() in _CODE_SUFFIXES or re.search(
            r"(^|/)(src/|app/|apps/|packages/|frontend/|backend/)",
            path.replace("\\", "/"),
        ):
            return {
                "action": "block",
                "message": (
                    f"research-bot blocks product-code writes ({tool_name} → {path}). "
                    "Write cited findings under notes/, research/, briefs/, or a "
                    ".md/.txt/.bib artifact."
                ),
            }
    if tool_name in _TERMINAL_TOOLS:
        command = str(args.get("command") or args.get("code") or "")
        if _SCAFFOLD.search(command):
            return {
                "action": "block",
                "message": (
                    "Blocked terminal command that looks like application scaffolding. "
                    "Use terminal for research lookups only."
                ),
            }
    return None
