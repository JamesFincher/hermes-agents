# research-bot instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)

This file is the **execution join** for this profile only. Official pages James shared — not training data. Do not copy this plugin, these tools, or these skills to the next profile.

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

| Layer | This profile |
| --- | --- |
| Plugin | `plugins/research-bot/` — host package (`plugin.yaml` + `register(ctx)`). Not a tool. |
| `plugins.enabled` | `[research-bot]` |
| Toolset | `research-bot` (this profile only) |
| Tools the plugin registers | `resolve_library`, `docs_query`, `source_ledger_add`, `source_ledger_list`, `cite_source`, `source_ledger_check` |
| MCP backend | server `context7`; `mcp_allowlist: [context7]`; plugin calls via `ctx.call_mcp` |
| Skills | `literature-review`, `source-triage`, `claim-check` in profile `skills/` |
| Skill gate | `requires_toolsets: [research-bot]` + `requires_tools: [resolve_library, docs_query, cite_source]` |

---

## Settled: memory

`memory.provider: honcho`. Unique `aiPeer`: `research-bot`. Host `hermes.research-bot`. `recallMode: hybrid`. `pinUserPeer: true` is official and gateway-only. Not in `plugins.enabled`. Do not write a second memory provider. Do not expand these knobs. https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin

---

## 1. Profile identity + skills index

https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

**SOUL** (`$HERMES_HOME/SOUL.md`) is identity and tone only. First slot in the cached **stable** system prompt. Not a tool procedure. Not a skill. Not a plugin. Subagents skip SOUL (`skip_context_files` → `DEFAULT_AGENT_IDENTITY`).

**Skills index** is also stable (cached). Description frontmatter is the index text — when-to-use must be unmistakable. Bodies load via `skill_view`. Required sections: When to Use, Quick Reference, Procedure, Pitfalls, Verification. Primary library lives in profile `skills/`. `ctx.register_skill` is hidden `plugin:skill` — do not put the primary library there.

System prompt is built **once** and reused. Rebuild only if model, provider, cwd, or platform changes, or compression rebuild. Turn-varying ledger text must not live in SOUL or `config.yaml` `system_message`.

---

## 2. Dedicated native plugin

https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access

The adding-tools page is **built-in core only** (`tools/` + `toolsets.py`). Custom tools **must** use the plugin route. Never patch Hermes core.

Native path: `plugin.yaml` + `__init__.py` `register(ctx)`. Not Portable Agent Plugins v1 (`plugin.json`). This plugin **registers** tools, hooks, and settings. It is not itself a tool.

Required files: `plugin.yaml`, `__init__.py`, `schemas.py`, `tools.py`. Schema descriptions say **when to call** `resolve_library` / `docs_query` / `cite_source`. Handlers return a `json.dumps` string, never raise, take `**kwargs`, read `task_id` from kwargs. Ledger writes are thread-safe (`plugin-data/`, concurrent tool pool).

`distribution_owned` includes `plugins/` so install copies a flat `research-bot` plugin into this profile’s `HERMES_HOME`.

`ctx.llm` is **out of band**. No tool loop. Does not replace `register_tool`. See §6.

---

## 3. MCP as a backend the plugin calls

The model’s primary tools are the ones this plugin registered. Context7 is a connected MCP server the **plugin** calls.

- Server name: `context7`. Do not set `tools.include: []` or `enabled: false`.
- `ctx.call_mcp("context7", "resolve-library-id", …)` and `ctx.call_mcp("context7", "query-docs", …)` — unsanitized MCP names.
- Facade tools the model calls: `resolve_library`, `docs_query`.
- `plugins.entries.research-bot.mcp_allowlist: [context7]`. No wildcards.
- Skills and the user-message contract forbid raw `mcp_*`. Do not put `CONTEXT7_API_KEY` on a skill.

Sanitize of MCP-named tools is **UNVERIFIED**. Do not harvest or block raw `mcp_*`.

---

## 4. Agent loop + hooks

https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly

### Turn lifecycle

`chat()` → `run_conversation()`. Turn: append user → reuse cached system prompt → preflight compression if >50% → build API messages → ephemeral layers → interruptible API call → if `tool_calls`, execute and loop; if text, persist and return.

Registry tools: resolve → `pre_tool_call` → approval if dangerous → handler → `post_tool_call` → `role=tool`. Concurrent `ThreadPoolExecutor`; `clarify` sequential.

Agent-level tools intercepted **before** the registry: `todo`, `memory`, `session_search`, `delegate_task`. Do not hook-police them.

`IterationBudget` default 500. Compression: flush memory first, `protect_last_n` 20, never split tool/result pairs, child session lineage. Ledger path `<HERMES_HOME>/plugin-data/research-bot/source-ledger.json` must survive that lineage.

### Prompt tiers

Cached system: **stable** (SOUL, tool guidance, skills index) → **context** (optional `system_message` + one project file) → **volatile** (MEMORY/USER snapshots, first-turn external memory block, timestamp).

**API-call-time only** (not cached system): `ephemeral_system_prompt`, prefill, gateway overlays, later-turn external recall on the **user** message, `pre_llm_call` on the **user** message (10k cap).

This repo’s root `AGENTS.md` is Cursor workflow, not Hermes runtime.

### Hooks this plugin registers

| Hook | Job |
| --- | --- |
| `on_session_start` | Init the source ledger |
| `pre_llm_call` | Inject research contract + live ledger digest on the **user** message (under 10k) |
| `pre_tool_call` | Block product-code writes / scaffolding terminal. Return `None` for intercepted agent tools |
| `post_tool_call` | Fires for **all** tools. Backup-harvest facade names only |

No `register_middleware` in v1. No `ctx.llm` on these hooks.

---

## 5. Skills that require the plugin toolset

https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

Each research `SKILL.md`:

- `description`: when to load, one line
- `metadata.hermes.requires_toolsets: [research-bot]`
- `metadata.hermes.requires_tools: [resolve_library, docs_query, cite_source]` (exact registered names)
- `metadata.hermes.related_skills`: the other two
- Procedure **names** those tools, forbids raw `mcp_*`, and says `cite_source` after every claim
- Hide if ANY listed toolset/tool is missing. Missing env does **not** hide.
- No `CONTEXT7_API_KEY` in skill env. No blueprint. `inline_shell` off. `scripts/` only if parsing cannot be the plugin.

Local test (not CI): `hermes chat --toolsets skills -q "Use the X skill to do Y"`

---

## 6. `ctx.llm` uses

https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access

Out of band. Default: user’s active provider/model. No `allow_*` grants in v1. `purpose=` required if we call it frequently. Cost is the user’s paid provider.

**v1: do not call `ctx.llm`.** Agent-facing work stays the registered tools + skills.

Later (not now): `complete_structured` + `json_schema` to type a Context7 blob for the ledger. If `parsed` is `None`, use `result.text`. `register_auxiliary_task` only if a cheap classifier is needed.

---

## 7. Subagent constraints

https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api

`ctx.subagent_lifecycle.launch` only during an active agent turn. Outside a turn: fail-closed `No active Hermes parent session`. Same child path as `delegate_task`. Children skip SOUL — paste the contract into `goal`/`context`. `allowed_toolsets` **narrows**; unknown or parent-broadening rejected. Do not give a research child write or product toolsets.

v1 does not launch children from this plugin. Handles are opaque; after process restart reconnect is `RECONNECT_UNAVAILABLE`. Terminal results 32k, no transcripts.
