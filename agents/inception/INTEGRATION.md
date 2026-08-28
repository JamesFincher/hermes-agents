# inception instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)

This file is the **execution join** for this profile only. Official pages — not training data. This profile must not enable `hdr`. Do not copy this plugin, these tools, or these skills to the next profile.

## Nine surfaces

| Surface | This profile |
| --- | --- |
| SOUL | Identity only. Profile librarian. No tool names. |
| config.yaml | Cited knobs. Sweep in the spec. Bundle `factory`. |
| MCP | Server `context7` only. Connected so `ctx.call_mcp` works. |
| Plugin | `plugins/inception/`. Host package. Not a tool. |
| Tools | The inception plugin registers `docs_resolve`, `docs_ask`, `probe_knob`, `plan_start`, `investigate_surface`, `write_canvas`, `write_spec`, `check_plan`, `scaffold_profile`, `check_profile`. |
| Skills | `plan-profile` (steps 0–4), `author-profile` (steps 5–10 after the gate), `probe-knob`, `review-profile`. |
| Delegation | Rejected. Not in the bundle. |
| Memory | `memory.provider: honcho`. See the settled paragraph. |
| Distribution + eval | Path install. `evals/tasks.jsonl`. CI unit tests. |

Say: "the inception plugin registers the `check_plan` tool." Never collapse PLUGIN and TOOL into one noun. Scaffold is blocked until that tool returns ok.

| Official page | URL |
| --- | --- |
| Agent Loop Internals | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| Prompt Assembly | https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly |
| Adding Tools | https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools |
| Plugins (native) | https://hermes-agent.nousresearch.com/docs/developer-guide/plugins |
| Creating Skills | https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills |
| Plugin LLM Access | https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access |
| Subagent Lifecycle API | https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api |
| Memory Provider Plugin | https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin |
| Tools (user) | https://hermes-agent.nousresearch.com/docs/user-guide/features/tools |
| Toolsets Reference | https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference |
| Web Search | https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search |
| Configuration | https://hermes-agent.nousresearch.com/docs/user-guide/configuration |

Context7 this pass: `/nousresearch/hermes-agent`. Honcho only for the settled memory paragraph: `/plastic-labs/honcho`.

## Settled: memory

`memory.provider: honcho`. Unique `aiPeer`: `hermes.inception`. Host `hermes.inception`. `recallMode: hybrid`. `pinUserPeer: true` is official and gateway-only. Not in `plugins.enabled`. Do not write a second memory provider.

## Custom surface

Five §4 patterns ship:

1. **Intercept-and-distil** — `transform_tool_result` bounds `docs_resolve` / `docs_ask`.
2. **Fence** — `pre_tool_call` blocks reserved names, secret files, HARD governor writes, and any write under `agents/<name>/` until `check_plan` is ok. Policy. Fail closed with a reason.
3. **Free output** — `transform_llm_output` appends a factory footer.
4. **Ledger** — `plugin-data/inception/factory.json`, `version: 2`. One plan record per target name.
5. **Governor** — `pre_api_request` counts requests and input tokens.

Static contract is a prompt section (`after_memory`). Volatile digest is `pre_llm_call`, capped at 800 characters by the plugin.

Handler contract: `json.dumps` string, never raise, `handler(args, **kwargs)`, errors `{"error":"…"}`. [DOC] https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools

`ctx.llm` is not used. Official Plugin LLM Access stays available and unused.

## MCP as a backend

The model calls facade tools. The plugin calls `ctx.call_mcp("context7", …)`. A Context7 result becomes a ledger card only when it carries an openable `https://` URL. No first-party OpenAlex, PubMed, or Wayback server.

## Agent loop + hooks

`pre_llm_call` injects the digest on the user message. `pre_tool_call` is the fence. `transform_tool_result` distils docs. Other hooks fail open.

## Subagent constraints

Fan-out is rejected. `delegate_task` is not in the enabled bundle. Children are out of scope.
