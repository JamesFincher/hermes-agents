# Integration notes

**Source of truth:** [`PROFILE-PLAYBOOK.md`](PROFILE-PLAYBOOK.md)

Each profile’s `agents/<name>/INTEGRATION.md` is that profile’s join map: plugin name, toolset, MCP allowlist, skill `requires_tools`, and any official-page locks that profile must obey.

Copy the playbook’s **method**, not another profile’s plugin, tools, or skills.

`research-bot` locks the official join in [`../agents/research-bot/INTEGRATION.md`](../agents/research-bot/INTEGRATION.md), citing the pages below. Native plugin path only. Skills live in the profile `skills/` index. Do not patch Hermes `tools/` or ship a second memory provider.

## Official pages (cite these, not training data)

- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access
- https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api
- https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin

## Creating skills (priority)

https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

Skill = instructions + shell + existing tools. Tool = auth, must-execute-precisely processing, binary, streaming. Primary library is profile `skills/` (indexed). `ctx.register_skill` is hidden `plugin:skill`. Required sections: When to Use, Quick Reference, Procedure, Pitfalls, Verification. Hide if ANY `requires_*` is missing. Missing `required_environment_variables` does **not** hide. Do not put `CONTEXT7_API_KEY` on a skill. Do not enable `inline_shell`. Do not add a blueprint unless a scheduled job was requested.

## Plugin LLM access

https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access

`ctx.llm` is out of band. No tool loop. Does not replace `register_tool`. Do not loop it on every hook. No `allow_*` grants unless needed.

## Subagent lifecycle

https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api

`ctx.subagent_lifecycle.launch` only during an active turn. Same child path as `delegate_task`. Children skip SOUL. `allowed_toolsets` narrows only. Do not give a research child write or product toolsets.

## Memory provider plugin

https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin

Single-select. Honcho is `memory.provider`. Do not write a second memory provider. Memory-provider skills (`provider:skill`) are not the primary library.
