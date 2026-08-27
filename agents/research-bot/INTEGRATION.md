# research-bot instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)

This file is the **execution join** for this profile only. Official pages James shared — not training data. Do not copy this plugin, these tools, or these skills to the next profile.

## Three surfaces — never collapse

| Surface | Official object | This profile |
| --- | --- | --- |
| **SKILL** | Indexed `SKILL.md` recipe. Loaded via `skill_view`. No Python. Procedure names **tools**. | `deep-research-run`, `source-triage`, `claim-audit`, `literature-sweep`, `web-fallback-fetch` |
| **TOOL** | Registry schema + handler the model invokes. Also builtins and `mcp_*`. Do not patch `tools/` or `toolsets.py`. | The hdr plugin **registers** plan, evidence, citation, retrieval, and fan-out tools |
| **PLUGIN** | `plugin.yaml` + `register(ctx)` host package. May register tools **and** hooks **and** middleware **and** config/state. **Not itself a tool.** | `plugins/hdr/` |

Say: "the hdr plugin registers the `research_plan` tool." Never collapse PLUGIN and TOOL into one noun.

| Official page | URL |
| --- | --- |
| Agent Loop Internals | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| Prompt Assembly | https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly |
| Adding Tools | https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools |
| Plugins (native) | https://hermes-agent.nousresearch.com/docs/developer-guide/plugins |
| Creating Skills (priority) | https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills |
| Plugin LLM Access | https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access |
| Subagent Lifecycle API | https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api |
| Memory Provider Plugin | https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin |
| Tools (user) | https://hermes-agent.nousresearch.com/docs/user-guide/features/tools |
| Toolsets Reference | https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference |
| Web Search | https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search |
| Web Search Provider Plugins | https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin |
| Configuration | https://hermes-agent.nousresearch.com/docs/user-guide/configuration |

Context7 library this pass: `/nousresearch/hermes-agent` (resolve + query-docs). Official pages above are the join. Do not invent knobs. Facts: [`../../docs/HERMES-FACTS.md`](../../docs/HERMES-FACTS.md).

| Layer | This profile |
| --- | --- |
| Plugin | `plugins/hdr/` — host package (`plugin.yaml` + `register(ctx)`). Not a tool. |
| `plugins.enabled` | `[hdr]` |
| Toolset | `hdr` (this profile only) |
| Tools the plugin registers | `research_plan`, `gap_scan`, `evidence_*`, `claim_verify`, `conflict_report`, `cite_source`, `worker_brief`, `worker_harvest`, `resolve_library`, `docs_query`, `scholar_search`, `archive_lookup` |
| MCP backend | server `context7`; `mcp_allowlist: [context7]`; plugin calls via `ctx.call_mcp` |
| Skills | five disjoint recipes in profile `skills/` |
| Gather | Builtins `web_search` / `web_extract`. Browser and HTTP scholar/archive are fallbacks. Keyless on. |

---

## Settled: memory

`memory.provider: honcho`. Unique `aiPeer`: `research-bot`. Host `hermes.research-bot`. `recallMode: hybrid`. `pinUserPeer: true` is official and gateway-only. Not in `plugins.enabled`. Do not write a second memory provider. Do not expand these knobs. https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin

---

## Profile identity + skills index

https://hermes-agent.nousresearch.com/docs/guides/use-soul-with-hermes
https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

**SOUL** (`$HERMES_HOME/SOUL.md`) is PRIMARY IDENTITY. First slot in the cached **stable** system prompt. It replaces the built-in default identity. Not a tool procedure. Not a skill. Not a plugin. Do not collapse it. Subagents skip SOUL (`skip_context_files` → `DEFAULT_AGENT_IDENTITY`). Paste the contract into `goal` and `context` when you delegate.

**Skills index** is also stable (cached). Description frontmatter is the index text. Bodies load via `skill_view`. Required sections: When to Use, Quick Reference, Procedure, Pitfalls, Verification. Gating keys live under `metadata.hermes`. Scripts use `${HERMES_SKILL_DIR}`. `web-fallback-fetch` sets `fallback_for_tools: [web_extract]`. Primary library lives in profile `skills/`. `ctx.register_skill` is hidden `plugin:skill` — do not put the primary library there.

System prompt is built **once** and reused. Turn-varying digest text lives in `pre_llm_call`, not SOUL or `config.yaml` `system_message`. Static HDR method/effort/integrity live in `register_system_prompt_section`.

---

## Dedicated native plugin

`plugins/hdr/` is a general plugin. `plugin.yaml` + `register(ctx)`. Toolset `hdr`. Handler contract: `json.dumps` string, never raise, `handler(args, **kwargs)`, `ctx.call_mcp` envelope `{ok,result}|{ok,error}`. Store is `<HERMES_HOME>/plugin-data/hdr/`.

---

## MCP as a backend

The model calls facade tools. The plugin calls `ctx.call_mcp("context7", …)`. A Context7 result enters the ledger only when it carries an openable `https://` URL. There is no official OpenAlex, PubMed, or Wayback Hermes server. Scholar and archive use HTTP.

---

## Agent loop + hooks

`pre_llm_call` injects a ≤1200-character digest on the user message. `transform_tool_result` is the Evidence Bus. `pre_tool_call` is dedupe, write allowlist, Citation Gate, and the governor fence. `pre_verify` does not fire for markdown-only turns.

---

## ctx.llm

Official Plugin LLM Access. Out of band. Trust-gated. Optional citation pass. Not a substitute for `claim_verify`.

---

## Subagent constraints

Children inherit parent toolsets and cannot widen them. Leaf children cannot call `delegate_task`, `clarify`, `memory`, `send_message`, or `cronjob`. Both roles keep `execute_code`. `pre_tool_call` may block `delegate_task` when the governor is AMBER, RED, or HARD. Live transcripts: `<hermes_home>/cache/delegation/live/<delegation_id>/task-<n>.log`.
