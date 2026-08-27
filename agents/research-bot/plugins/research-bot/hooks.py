"""research-bot workflow hooks. Every handler accepts **kwargs.

Official signatures:
https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
pre_llm_call injects onto the user message, not the system prompt.
"""

from __future__ import annotations

from typing import Any

from . import ledger, policy

RESEARCH_CONTRACT = (
    "[research-bot] Use the research-bot source ledger. After retrieving a source, "
    "call source_ledger_add. Before citing, call source_ledger_cite and only use "
    "those formatted entries. Before asserting a factual claim, call "
    "source_ledger_check. Do not invent citations. Do not write product code; "
    "research artifacts only (notes/, research/, briefs/, .md/.txt/.bib)."
)


def on_session_start(session_id: str, model: str, platform: str, **kwargs: Any) -> None:
    """Initialize the profile-scoped ledger for this session."""
    del session_id, model, platform, kwargs
    try:
        ledger.init_ledger()
    except Exception:
        return


def pre_llm_call(session_id: str, user_message: str, **kwargs: Any) -> dict[str, str] | None:
    """Inject the research contract onto the user message (keeps the system-prompt cache)."""
    del session_id, kwargs
    if RESEARCH_CONTRACT in (user_message or ""):
        return None
    return {"context": RESEARCH_CONTRACT}


def pre_tool_call(
    tool_name: str,
    args: dict[str, Any],
    task_id: str,
    **kwargs: Any,
) -> dict[str, str] | None:
    """Block product-code writes; allow research artifacts."""
    del task_id, kwargs
    return policy.write_policy(tool_name, args)


def post_tool_call(
    tool_name: str,
    args: dict[str, Any],
    result: str,
    task_id: str,
    duration_ms: int,
    **kwargs: Any,
) -> None:
    """Harvest URLs from retrieval tools into the source ledger."""
    del task_id, duration_ms, kwargs
    if tool_name.startswith("source_ledger_"):
        return
    try:
        ledger.harvest_from_tool(tool_name, args, result)
    except Exception:
        return
