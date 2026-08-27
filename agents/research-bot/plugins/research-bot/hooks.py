"""Hooks. Official signatures accept **kwargs.

pre_llm_call is API-call-time only: appended to the current-turn user
message, not written into the cached system prompt (stable/context/volatile).
https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks

todo/memory/session_search/delegate_task are intercepted before the
registry — do not police them here.
https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
"""

from __future__ import annotations

from typing import Any

from . import ledger, policy

CONTRACT = (
    "RESEARCH CONTRACT (user-message injection; cached SOUL/system_message "
    "must not carry turn-varying text):\n"
    "- Use resolve_library and docs_query for Context7. Do not call raw mcp_* tools.\n"
    "- After a non-Context7 retrieve, call source_ledger_add. After every claim, "
    "cite_source. Before a fact, source_ledger_check.\n"
    "- Do not invent knobs. Do not write product application code."
)


def on_session_start(session_id: str, model: str, platform: str, **kwargs: Any) -> None:
    del session_id, model, platform, kwargs
    try:
        ledger.init_ledger()
    except Exception:
        return


def pre_llm_call(
    session_id: str,
    user_message: str,
    conversation_history: list[Any] | None = None,
    is_first_turn: bool = False,
    model: str = "",
    platform: str = "",
    **kwargs: Any,
) -> dict[str, str] | None:
    del session_id, conversation_history, is_first_turn, model, platform, kwargs
    try:
        text = f"{CONTRACT}\n{ledger.digest()}"
        if len(text) > 10000:
            text = text[:9900] + "\n[truncated]"
        if text in (user_message or ""):
            return None
        return {"context": text}
    except Exception:
        return None


def pre_tool_call(
    tool_name: str,
    args: dict[str, Any],
    task_id: str,
    **kwargs: Any,
) -> dict[str, str] | None:
    del task_id, kwargs
    try:
        return policy.write_policy(tool_name, args if isinstance(args, dict) else {})
    except Exception:
        return None


def post_tool_call(
    tool_name: str,
    args: dict[str, Any],
    result: str,
    task_id: str,
    duration_ms: int = 0,
    **kwargs: Any,
) -> None:
    """Official: post_tool_call fires for ALL tools. Harvest facade only."""
    del task_id, duration_ms, kwargs
    if tool_name not in {"resolve_library", "docs_query"}:
        return
    try:
        parsed_args = args if isinstance(args, dict) else {}
        query = str(parsed_args.get("query") or "")
        if tool_name == "resolve_library" and query:
            ledger.add_source(
                url=f"context7://resolve-library-id?q={query}",
                title=f"Context7 resolve_library: {query[:80]}",
                quote=str(result)[:400],
                kind="docs",
                origin="post_tool_call",
            )
        elif tool_name == "docs_query":
            library_id = str(parsed_args.get("library_id") or "")
            ledger.add_source(
                url=f"context7://query-docs?library={library_id}",
                title=f"Context7 docs_query: {query[:80]}",
                quote=str(result)[:400],
                kind="docs",
                origin="post_tool_call",
            )
    except Exception:
        return
