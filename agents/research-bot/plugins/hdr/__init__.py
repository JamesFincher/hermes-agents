"""hdr — profile-local general plugin for research-bot.

Official: plugin.yaml + register(ctx).
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

This PLUGIN registers TOOLS and hooks. It is not a tool.
Skills live in profile skills/ and are not this package.
Do not copy to other agents.
"""

from __future__ import annotations

from typing import Any

from . import hooks, runtime, schemas
from .tools import (
    archive_lookup,
    claim_verify,
    cite_source,
    conflict_report,
    docs_query,
    evidence_add,
    evidence_read,
    evidence_search,
    evidence_stats,
    gap_scan,
    research_plan,
    resolve_library,
    scholar_search,
    worker_brief,
    worker_harvest,
)

_HANDLERS = {
    "research_plan": research_plan,
    "gap_scan": gap_scan,
    "evidence_add": evidence_add,
    "evidence_search": evidence_search,
    "evidence_read": evidence_read,
    "evidence_stats": evidence_stats,
    "claim_verify": claim_verify,
    "conflict_report": conflict_report,
    "cite_source": cite_source,
    "worker_brief": worker_brief,
    "worker_harvest": worker_harvest,
    "resolve_library": resolve_library,
    "docs_query": docs_query,
    "scholar_search": scholar_search,
    "archive_lookup": archive_lookup,
}


def register(ctx: Any) -> None:
    runtime.set_ctx(ctx)
    for schema in schemas.ALL:
        name = str(schema["name"])
        ctx.register_tool(
            name=name,
            toolset=runtime.TOOLSET,
            schema=schema,
            handler=_HANDLERS[name],
        )
    hooks.register_sections(ctx)
    ctx.register_hook("on_session_start", hooks.on_session_start)
    ctx.register_hook("on_session_end", hooks.on_session_end)
    ctx.register_hook("on_session_finalize", hooks.on_session_finalize)
    ctx.register_hook("on_session_reset", hooks.on_session_reset)
    ctx.register_hook("pre_llm_call", hooks.pre_llm_call)
    ctx.register_hook("pre_tool_call", hooks.pre_tool_call)
    ctx.register_hook("post_tool_call", hooks.post_tool_call)
    ctx.register_hook("transform_tool_result", hooks.transform_tool_result)
    ctx.register_hook("transform_terminal_output", hooks.transform_terminal_output)
    ctx.register_hook("transform_llm_output", hooks.transform_llm_output)
    ctx.register_hook("pre_api_request", hooks.pre_api_request)
    ctx.register_hook("post_api_request", hooks.post_api_request)
    ctx.register_hook("subagent_start", hooks.subagent_start)
    ctx.register_hook("subagent_stop", hooks.subagent_stop)
    ctx.register_hook("api_request_error", hooks.api_request_error)
