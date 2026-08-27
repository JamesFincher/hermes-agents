"""army-runtime — shared process layer for this factory's agents.

Official native plugin contract (Context7 /nousresearch/hermes-agent):
register(ctx) plus plugin.yaml. Tools return JSON strings and never raise.
Hooks accept **kwargs. Plugin state lives in plugin-data/, never this tree.

Skills stay in the normal skill index (agents/<name>/skills/, skills-tap/).
Do not bundle the primary library as plugin skills — those loads are hidden/opt-in.
"""

from __future__ import annotations

from typing import Any

from . import hooks, runtime, schemas, tools
from .middleware import tool_request_defaults


def register(ctx: Any) -> None:
    runtime.set_ctx(ctx)

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
        name="source_ledger_cite",
        toolset=runtime.TOOLSET,
        schema=schemas.SOURCE_LEDGER_CITE,
        handler=tools.source_ledger_cite,
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

    ctx.register_middleware("tool_request", tool_request_defaults)
