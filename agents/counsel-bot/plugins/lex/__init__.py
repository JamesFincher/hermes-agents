"""lex — the counsel-bot plugin.

Registers tools, hooks, and cache-safe system prompt sections. Hook order is
deliberate: policy gates are registered before observers so a block short
circuits before anything is written to the audit log as accepted.
"""
from __future__ import annotations
import logging

from . import runtime, schemas
from .tools import matter as t_matter, authority as t_auth, citation as t_cite, draft as t_draft, plan as t_plan
from .hooks import prompt, intake, policy, governor, output, lifecycle, subagents

log = logging.getLogger("lex")

_TOOLS = {
    "matter_open": t_matter.matter_open,
    "matter_fact": t_matter.matter_fact,
    "set_hat": t_matter.set_hat,
    "authority_search": t_auth.authority_search,
    "authority_add": t_auth.authority_add,
    "authority_read": t_auth.authority_read,
    "authority_status": t_auth.authority_status,
    "cite_check": t_cite.cite_check,
    "cite_format": t_cite.cite_format,
    "conflict_report": t_cite.conflict_report,
    "draft_scaffold": t_draft.draft_scaffold,
    "draft_check": t_draft.draft_check,
    "deadline_compute": t_draft.deadline_compute,
    "issue_plan": t_plan.issue_plan,
    "worker_brief": t_plan.worker_brief,
}


def register(ctx):
    runtime.bind(ctx)

    for name, handler in _TOOLS.items():
        ctx.register_tool(
            name=name,
            description=schemas.DESCRIPTIONS[name],
            parameters=schemas.SCHEMAS[name],
            handler=handler,
            toolset="lex",
        )

    # Static guidance: paid once per session, frozen on compaction.
    ctx.register_system_prompt_section(
        "lex.gates", prompt.section_gates, position="after_memory", max_chars=2400
    )
    ctx.register_system_prompt_section(
        "lex.method", prompt.section_method, position="after_memory", max_chars=1800
    )

    # Directive / transform hooks first.
    ctx.register_hook("pre_tool_call", policy.pre_tool_call)
    ctx.register_hook("transform_tool_result", intake.transform_tool_result)
    ctx.register_hook("transform_terminal_output", intake.transform_terminal_output)
    ctx.register_hook("transform_llm_output", output.transform_llm_output)
    ctx.register_hook("pre_llm_call", prompt.pre_llm_call)

    # Observers.
    ctx.register_hook("post_tool_call", governor.post_tool_call)
    ctx.register_hook("pre_api_request", governor.pre_api_request)
    ctx.register_hook("post_api_request", governor.post_api_request)
    ctx.register_hook("subagent_start", subagents.subagent_start)
    ctx.register_hook("subagent_stop", subagents.subagent_stop)
    ctx.register_hook("on_session_start", lifecycle.on_session_start)
    ctx.register_hook("on_session_end", lifecycle.on_session_end)

    log.info("lex registered: %d tools, 12 hooks, 2 prompt sections", len(_TOOLS))
