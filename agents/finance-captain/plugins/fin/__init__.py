"""fin — the finance-captain plugin."""
from __future__ import annotations
import logging

from . import runtime, schemas
from .tools import entity as t_ent, data as t_data, analysis as t_an, report as t_rep, mutate as t_mut
from .hooks import prompt, intake, policy, governor, output, lifecycle, subagents

log = logging.getLogger("fin")

_TOOLS = {
    "entity_open": t_ent.entity_open,
    "period_manage": t_ent.period_manage,
    "snapshot_pull": t_data.snapshot_pull,
    "snapshot_diff": t_data.snapshot_diff,
    "ledger_query": t_data.ledger_query,
    "metric_registry": t_an.metric_registry,
    "metric_compute": t_an.metric_compute,
    "budget_manage": t_an.budget_manage,
    "variance_report": t_an.variance_report,
    "cash_forecast": t_an.cash_forecast,
    "anomaly_scan": t_an.anomaly_scan,
    "recon_tieout": t_an.recon_tieout,
    "figure_check": t_rep.figure_check,
    "report_scaffold": t_rep.report_scaffold,
    "report_check": t_rep.report_check,
    "audit_trail": t_rep.audit_trail,
    "mutation_propose": t_mut.mutation_propose,
    "mutation_apply": t_mut.mutation_apply,
}


def register(ctx):
    runtime.bind(ctx)

    for name, handler in _TOOLS.items():
        ctx.register_tool(name=name, description=schemas.DESCRIPTIONS[name],
                          schema=schemas.SCHEMAS[name], handler=handler, toolset="fin")

    ctx.register_system_prompt_section("fin.gates", prompt.section_gates,
                                       position="after_memory", max_chars=2400)
    ctx.register_system_prompt_section("fin.method", prompt.section_method,
                                       position="after_memory", max_chars=1800)

    ctx.register_hook("pre_tool_call", policy.pre_tool_call)
    ctx.register_hook("transform_tool_result", intake.transform_tool_result)
    ctx.register_hook("transform_terminal_output", intake.transform_terminal_output)
    ctx.register_hook("transform_llm_output", output.transform_llm_output)
    ctx.register_hook("pre_llm_call", prompt.pre_llm_call)

    ctx.register_hook("post_tool_call", governor.post_tool_call)
    ctx.register_hook("pre_api_request", governor.pre_api_request)
    ctx.register_hook("post_api_request", governor.post_api_request)
    ctx.register_hook("subagent_start", subagents.subagent_start)
    ctx.register_hook("subagent_stop", subagents.subagent_stop)
    ctx.register_hook("on_session_start", lifecycle.on_session_start)
    ctx.register_hook("on_session_end", lifecycle.on_session_end)

    log.info("fin registered: %d tools, 12 hooks, 2 prompt sections", len(_TOOLS))
