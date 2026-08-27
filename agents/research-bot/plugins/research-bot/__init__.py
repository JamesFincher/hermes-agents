"""research-bot — profile-local general plugin.

Official: plugin.yaml + register(ctx).
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

This PLUGIN registers TOOLS and hooks. It is not a tool.
Skills live in profile skills/ and are not this package.
Do not copy to other agents.
"""

from __future__ import annotations

from typing import Any

from . import hooks, runtime, schemas, tools


def register(ctx: Any) -> None:
    runtime.set_ctx(ctx)

    ctx.register_tool(
        name="resolve_library",
        toolset=runtime.TOOLSET,
        schema=schemas.RESOLVE_LIBRARY,
        handler=tools.resolve_library,
    )
    ctx.register_tool(
        name="docs_query",
        toolset=runtime.TOOLSET,
        schema=schemas.DOCS_QUERY,
        handler=tools.docs_query,
    )
    ctx.register_tool(
        name="source_ledger_add",
        toolset=runtime.TOOLSET,
        schema=schemas.SOURCE_LEDGER_ADD,
        handler=tools.source_ledger_add,
    )
    ctx.register_tool(
        name="source_ledger_list",
        toolset=runtime.TOOLSET,
        schema=schemas.SOURCE_LEDGER_LIST,
        handler=tools.source_ledger_list,
    )
    ctx.register_tool(
        name="cite_source",
        toolset=runtime.TOOLSET,
        schema=schemas.CITE_SOURCE,
        handler=tools.cite_source,
    )
    ctx.register_tool(
        name="source_ledger_check",
        toolset=runtime.TOOLSET,
        schema=schemas.SOURCE_LEDGER_CHECK,
        handler=tools.source_ledger_check,
    )

    ctx.register_hook("on_session_start", hooks.on_session_start)
    ctx.register_hook("pre_llm_call", hooks.pre_llm_call)
    ctx.register_hook("pre_tool_call", hooks.pre_tool_call)
    ctx.register_hook("post_tool_call", hooks.post_tool_call)
