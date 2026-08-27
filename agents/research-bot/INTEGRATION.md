# research-bot instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)

This file is the **execution join** for this profile only. Official pages James shared — not training data. Do not copy this plugin, these tools, or these skills to the next profile.

## Three surfaces — never collapse

| Surface | Official object | This profile |
| --- | --- | --- |
| **SKILL** | Indexed `SKILL.md` recipe. Loaded via `skill_view`. No Python. Procedure names **tools**. | `skills/literature-review`, `source-triage`, `claim-check` |
| **TOOL** | Registry schema + handler the model invokes. Also builtins and `mcp_*`. Do not patch `tools/` or `toolsets.py`. | The research-bot plugin **registers** `resolve_library`, `docs_query`, `source_ledger_add`, `source_ledger_list`, `cite_source`, `source_ledger_check` |
| **PLUGIN** | `plugin.yaml` + `register(ctx)` host package. May register tools **and** hooks **and** middleware **and** config/state. **Not itself a tool.** | `plugins/research-bot/` |

Say: "the research-bot plugin registers the `resolve_library` tool." Never collapse PLUGIN and TOOL into one noun.

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

Context7 library this pass: `/nousresearch/hermes-agent` (resolve + query-docs). Official pages above are the join. Do not invent knobs.

| Layer | This profile |
| --- | --- |
| Plugin | `plugins/research-bot/` — host package (`plugin.yaml` + `register(ctx)`). Not a tool. |
| `plugins.enabled` | `[research-bot]` |
| Toolset | `research-bot` (this profile only) |
| Tools the plugin registers | `resolve_library`, `docs_query`, `source_ledger_add`, `source_ledger_list`, `cite_source`, `source_ledger_check` |
| MCP backend | server `context7`; `mcp_allowlist: [context7]`; plugin calls via `ctx.call_mcp` |
| Skills | `literature-review`, `source-triage`, `claim-check` in profile `skills/` |
| Skill gate | `requires_toolsets: [research-bot]` + `requires_tools: [resolve_library, docs_query, cite_source]`. Procedure names `web_search` / `web_extract`. |
| Gather | Builtins `web_search` / `web_extract`. `web.search_backend: searxng`. `web.extract_backend: firecrawl`. Keyless off. |

---

## Settled: gather

Search uses local SearXNG. Extract uses local Firecrawl on the deploy host. The model calls the builtins `web_search` and `web_extract`. This plugin does not register those tools. This plugin is not a search backend. Context7 is library docs only.

Set `SEARXNG_URL` and `FIRECRAWL_API_URL` on the deploy host. Never commit those values. Official: when `FIRECRAWL_API_URL` is set, `FIRECRAWL_API_KEY` is optional.

https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search
https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin
https://hermes-agent.nousresearch.com/docs/user-guide/configuration

---

## Settled: memory

`memory.provider: honcho`. Unique `aiPeer`: `research-bot`. Host `hermes.research-bot`. `recallMode: hybrid`. `pinUserPeer: true` is official and gateway-only. Not in `plugins.enabled`. Do not write a second memory provider. Do not expand these knobs. https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin

---

## 1. Profile identity + skills index

https://hermes-agent.nousresearch.com/docs/guides/use-soul-with-hermes
https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

**SOUL** (`$HERMES_HOME/SOUL.md`) is PRIMARY IDENTITY. First slot in the cached **stable** system prompt. It replaces the built-in default identity. Not a tool procedure. Not a skill. Not a plugin. Do not collapse it. Subagents skip SOUL (`skip_context_files` → `DEFAULT_AGENT_IDENTITY`). Paste the contract into `goal` and `context` when you delegate.

**Skills index** is also stable (cached). Description frontmatter is the index text — when-to-use must be unmistakable. Bodies load via `skill_view`. Required sections: When to Use, Quick Reference, Procedure, Pitfalls, Verification. Primary library lives in profile `skills/`. `ctx.register_skill` is hidden `plugin:skill` — do not put the primary library there.

System prompt is built **once** and reused. Rebuild only if model, provider, cwd, or platform changes, or compression rebuild. Turn-varying ledger text must not live in SOUL or `config.yaml` `system_message`.

---

## 2. Dedicated native plugin

https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access

The adding-tools page is **built-in core only** (`tools/` + `toolsets.py`). A custom tool **must** be registered by this profile's plugin (`ctx.register_tool`). Never patch Hermes core.

Context7 (`/nousresearch/hermes-agent`) + https://hermes-agent.nousresearch.com/docs/developer-guide/plugins:

- `ctx.register_tool(name, toolset, schema, handler, check_fn=None, requires_env=None, is_async=False, description="", emoji="", override=False)`
- Schema is flat: `{name, description, parameters:{type:object, properties, required}}`
- Handler: `(args: dict, **kwargs) -> str`. Always `json.dumps`. Errors `{"error":"..."}`. Never raise. `task_id = kwargs.get("task_id")`
- `check_fn` False hides the tool from the model
- Every tool belongs to **exactly one** toolset. A tool is visible only when that toolset is enabled
- This plugin registers its tools with `toolset="research-bot"` (this profile only)

Native path: `plugin.yaml` + `__init__.py` `register(ctx)`. Not Portable Agent Plugins v1 (`plugin.json`). This plugin is the host package. It **registers** tools, hooks, and settings. It is not itself a tool.

Required files: `plugin.yaml`, `__init__.py`, `schemas.py`, `tools.py`. Schema descriptions say **when to call** `resolve_library` / `docs_query` / `cite_source`. Ledger writes are thread-safe (`plugin-data/`, concurrent tool pool).

`distribution_owned` includes `plugins/` so install copies a flat `research-bot` plugin into this profile’s `HERMES_HOME`.

`ctx.llm` is **out of band**. No tool loop. Does not replace `register_tool`. See §6.

---

## 3. MCP as a backend the plugin calls

The model invokes tools. Context7 is a connected MCP server the **plugin** calls; it is not a skill and not a Hermes tool.

Context7 (`/nousresearch/hermes-agent`) + official MCP/plugin pages:

- Server name: `context7`. Do not set `tools.include: []` (empty include is treated as unset). Do not set `enabled: false`.
- `ctx.call_mcp(server, tool, args, timeout=…)` — timeout clamped 1–600s. Envelope: `{ok, result}` or `{ok, error}`.
- This plugin calls unsanitized MCP names: `resolve-library-id`, `query-docs`.
- The research-bot plugin registers `resolve_library` and `docs_query`; those are the tools the model calls for Context7.
- User-guide MCP + native-mcp: model-facing MCP names look like `mcp_<server>_<tool>` (hyphens → underscores). Do not harvest or block those names. Skills `requires_tools` use facade names only.
- `plugins.entries.research-bot.mcp_allowlist: [context7]`. No wildcards.
- Do not put `CONTEXT7_API_KEY` on a skill.

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

## 5. Skills that require toolset `research-bot`

https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

Each research `SKILL.md`:

- `description`: when to load, one line
- `metadata.hermes.requires_toolsets: [research-bot]`
- `metadata.hermes.requires_tools: [resolve_library, docs_query, cite_source]` (exact registered names)
- `metadata.hermes.related_skills`: the other two
- Procedure **names** those tools plus `web_search` / `web_extract`, forbids raw `mcp_*`, and says `cite_source` after every claim. Source-triage ranks what the tools already return. Do not invent a ranker tool.
- Hide if ANY listed toolset/tool is missing. Missing env does **not** hide.
- No `CONTEXT7_API_KEY` in skill env. No blueprint. `inline_shell` off. `scripts/` only if parsing cannot be the plugin.

Local test (not CI): `hermes chat --toolsets skills -q "Use the X skill to do Y"`

---

## 6. `ctx.llm` uses

https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access

Out of band. Default: user’s active provider/model. No `allow_*` grants in v1. `purpose=` required if we call it frequently. Cost is the user’s paid provider.

**v1: do not call `ctx.llm`.** Agent-facing work stays tools (`ctx.register_tool`) plus indexed skills (`skill_view`). `ctx.llm` is neither.

Later (not now): `complete_structured` + `json_schema` to type a Context7 blob for the ledger. If `parsed` is `None`, use `result.text`. `register_auxiliary_task` only if a cheap classifier is needed.

---

## 7. Subagent constraints

https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api

`ctx.subagent_lifecycle.launch` only during an active agent turn. Outside a turn: fail-closed `No active Hermes parent session`. Same child path as `delegate_task`. Children skip SOUL — paste the contract into `goal`/`context`. `allowed_toolsets` **narrows**; unknown or parent-broadening rejected. Do not give a research child write or product toolsets.

v1 does not launch children from this plugin. Handles are opaque; after process restart reconnect is `RECONNECT_UNAVAILABLE`. Terminal results 32k, no transcripts.
