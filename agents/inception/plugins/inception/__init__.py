"""inception — profile-local general plugin.

Official: plugin.yaml + register(ctx).
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

This PLUGIN registers TOOLS and hooks. It is not a tool.
Skills live in profile skills/ and are not this package.
Do not copy to other agents.
"""

from __future__ import annotations

from typing import Any

from . import hooks, runtime, schemas
from .tools import check_profile, docs_ask, docs_resolve, probe_knob, scaffold_profile

_HANDLERS = {
    "docs_resolve": docs_resolve,
    "docs_ask": docs_ask,
    "probe_knob": probe_knob,
    "scaffold_profile": scaffold_profile,
    "check_profile": check_profile,
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
    ctx.register_hook("pre_llm_call", hooks.pre_llm_call)
    ctx.register_hook("pre_tool_call", hooks.pre_tool_call)
    ctx.register_hook("transform_tool_result", hooks.transform_tool_result)
    ctx.register_hook("transform_llm_output", hooks.transform_llm_output)
    ctx.register_hook("pre_api_request", hooks.pre_api_request)
    ctx.register_hook("post_api_request", hooks.post_api_request)
