# Integration notes

**Source of truth:** [`PROFILE-PLAYBOOK.md`](PROFILE-PLAYBOOK.md)

Each profile’s `agents/<name>/INTEGRATION.md` is that profile’s **execution join**: identity + skills index, the native plugin, the tools that plugin registers, MCP as a backend the plugin calls, agent-loop hooks, `ctx.llm` uses, subagent constraints.

**SKILL** = indexed `SKILL.md` (`skill_view`, no Python). **TOOL** = registry schema + handler (`ctx.register_tool`, or builtin, or `mcp_*`). **PLUGIN** = `plugin.yaml` + `register(ctx)` host package — not a tool. Say "the `<name>` plugin registers the `<tool>` tool." Never collapse PLUGIN and TOOL into one noun.

Copy the playbook’s **method**, not another profile’s plugin, tools, or skills.

Each profile is its own `HERMES_HOME`. Repo-root `plugins/` must not exist. Live process code lives only in that profile's `agents/<name>/plugins/`. research-bot ships plugin `hdr` (toolset `hdr`). The next profile writes its own plugin, toolset, and skills. Zero imports from `hdr`.

`research-bot` is planned in [`../agents/research-bot/INTEGRATION.md`](../agents/research-bot/INTEGRATION.md). Official pages (do not invent knobs):

- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access
- https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api
- https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin
- https://hermes-agent.nousresearch.com/docs/user-guide/features/tools
- https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search
- https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin
- https://hermes-agent.nousresearch.com/docs/user-guide/configuration

Context7 this pass: `/nousresearch/hermes-agent`. A **tool** is a registry schema + handler (`ctx.register_tool`). It is not a plugin and not a skill. Custom tools use the plugin route, not `tools/` + `toolsets.py`. Every tool belongs to one toolset. `ctx.call_mcp` returns `{ok, result}` or `{ok, error}`.

## Settled: memory

`memory.provider: honcho`. Unique `aiPeer` per profile. `pinUserPeer: true` (gateway-only). Hybrid recall. Not `plugins.enabled`. Do not write a second memory provider. Do not expand these knobs.

## Execution join (every specialized profile)

1. **Identity + skills index** — SOUL is tone. Skills in profile `skills/` (indexed). Stable cached tier. https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
2. **Dedicated native plugin** — `plugin.yaml` + `register(ctx)`. Do not patch core `tools/`. `ctx.llm` is out of band only.
3. **MCP as backend** — `ctx.call_mcp`. The model calls facade tools the plugin registered, not raw `mcp_*`.
4. **Agent loop + hooks** — turn-varying contract on `pre_llm_call` (user message). Do not hook-police intercepted agent tools.
5. **Skills require that plugin’s toolset** and name those tools in Procedure.
6. **Gather** — builtins `web_search` / `web_extract`. Local SearXNG for search. Local Firecrawl for extract. Keyless ring off. Do not add a search tool.
