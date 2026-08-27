# Integration notes

**Source of truth:** [`PROFILE-PLAYBOOK.md`](PROFILE-PLAYBOOK.md)

Each profile’s `agents/<name>/INTEGRATION.md` is that profile’s **execution join**: identity + skills index, the native plugin and the tools it registers, MCP as a backend the plugin calls, agent-loop hooks, `ctx.llm` uses, subagent constraints.

Copy the playbook’s **method**, not another profile’s plugin, tools, or skills.

`research-bot` is planned in [`../agents/research-bot/INTEGRATION.md`](../agents/research-bot/INTEGRATION.md). Official pages (do not invent knobs):

- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access
- https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api
- https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin

## Settled: memory

`memory.provider: honcho`. Unique `aiPeer` per profile. `pinUserPeer: true` (gateway-only). Hybrid recall. Not `plugins.enabled`. Do not write a second memory provider. Do not expand these knobs.

## Execution join (every specialized profile)

1. **Identity + skills index** — SOUL is tone. Skills in profile `skills/` (indexed). Stable cached tier. https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
2. **Dedicated native plugin** — `plugin.yaml` + `register(ctx)`. Do not patch core `tools/`. `ctx.llm` is out of band only.
3. **MCP as backend** — `ctx.call_mcp`. The model calls facade tools the plugin registered, not raw `mcp_*`.
4. **Agent loop + hooks** — turn-varying contract on `pre_llm_call` (user message). Do not hook-police intercepted agent tools.
5. **Skills require that plugin’s toolset** and name those tools in Procedure.
