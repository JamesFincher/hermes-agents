# research-bot instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)

This file is the join map for **this profile only**. Extracted from the official pages James shared — not from training data.

| Official page | URL |
| --- | --- |
| Agent Loop Internals | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| Prompt Assembly | https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly |
| Adding Tools | https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools |
| Plugins (native) | https://hermes-agent.nousresearch.com/docs/developer-guide/plugins |

| Layer | This profile |
| --- | --- |
| Plugin | `plugins/research-bot/` |
| `plugins.enabled` | `[research-bot]` |
| Toolset | `research-bot` |
| MCP | `context7` + `mcp_allowlist: [context7]` |
| Skills | `literature-review`, `source-triage`, `claim-check` |
| Skill gate | `requires_toolsets: [research-bot]` + facade / ledger tool names |
| Honcho | `memory.provider: honcho` (not `plugins.enabled`) |

Do not copy this plugin, these tools, or these skills to the next profile.

---

## Source A — Agent Loop

https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop

- Orchestrator is `AIAgent` in `run_agent.py`. Entry: `chat()` wraps `run_conversation()`.
- Turn: `task_id` → append user → build/reuse cached system prompt (`prompt_builder.py`) → preflight compression if >50% context → build API messages → ephemeral layers (budget/pressure) → cache markers → interruptible API call → if `tool_calls` execute then loop from build-API-messages; if text, persist session, flush memory, return.
- Tool path (registry tools): resolve `tools/registry.py` → `pre_tool_call` → `approval.py` if dangerous → handler → `post_tool_call` → append `role=tool`. Multiple `tool_calls` run concurrent `ThreadPoolExecutor`; interactive tools (`clarify`) force sequential. Results reinserted in original order.
- Agent-level tools intercepted **before** `handle_function_call` / registry: `todo`, `memory`, `session_search`, `delegate_task`. They return synthetic results and **do not** go through the registry. Do not rely on `pre_tool_call` / `post_tool_call` to police them.
- `IterationBudget` default 500 (`agent.max_turns`). Subagents get independent budgets capped at `delegation.max_iterations` (default 50).
- Compression: preflight >50%; gateway auto >85% between turns. Order: flush memory to disk **first**, summarize middle turns, `protect_last_n` (default 20), never split tool/result pairs, new session lineage id (child session).
- Persistence after each turn: session SQLite, `MEMORY.md` / `USER.md` flush. Interrupt abandons the API thread; no partial response enters history.

---

## Source B — Prompt Assembly

https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly

- Cached system prompt is **three tiers** joined `stable` → `context` → `volatile` (`agent/system_prompt.py`).
  - **stable:** `SOUL.md` identity, tool/model guidance, skills index, env hints, platform hints
  - **context:** caller `system_message` + **one** project context file (`.hermes.md` / `HERMES.md` walk-to-git-root, else `AGENTS.md` cwd, else `CLAUDE.md`, else `.cursorrules`). First match wins.
  - **volatile:** `MEMORY.md` snapshot, `USER.md` snapshot, external memory-provider block (Honcho), timestamp/session/model line
- Skills are **stable** (cached). Memory/Honcho snapshots are **volatile** but still in the cached system prompt, not mid-turn overlays.
- System prompt is built **once** (first turn) and reused from the session DB. Rebuild only if model, provider, cwd, or platform changes, or compression rebuild. **Not** because `MEMORY.md` or project files changed mid-session. Mid-session memory writes update disk only until rebuild.
- `skip_context_files` (subagent delegation): `SOUL.md` is **not** loaded; `DEFAULT_AGENT_IDENTITY` is used. The research contract must not live only in SOUL.
- SOUL is loaded from `$HERMES_HOME/SOUL.md`, security-scanned, truncated (20k floor, scales with window). `skip_soul` prevents double injection as a context file.
- **API-call-time only** (not cached system): `ephemeral_system_prompt`, prefill messages, gateway session overlays, later-turn Honcho/external recall on the **user** message, and `pre_llm_call` plugin context on the **user** message. Multiple plugin contexts concatenate.
- Concrete layer example from the page: 1 SOUL, 2 tool guidance, 3 Honcho static block, 4 optional system message, 5 MEMORY snapshot, 6 USER snapshot, 7 skills index (mandatory `skill_view`), 8 project context, 9 timestamp/session, 10 platform hint.
- Customize via SOUL / MEMORY / USER / project context / skills / optional system prompt / ephemeral overlays. Do **not** fork `prompt_builder.py`.
- `platform_hints` in `config.yaml` can append/replace per platform; lives in the stable tier (byte-stable, cache-safe).

---

## Locked consequences for this profile

1. Research contract + live ledger digest → plugin `pre_llm_call` on the **user** message. Never put turn-varying text in SOUL or in a config `system_message` (those are cached).
2. Skills stay in the stable index (when-to-use only). Bodies load via `skill_view`.
3. First-turn Honcho is the system volatile/static block. Later Honcho recall is user-message, same path as `pre_llm_call`. This plugin must not inject a second memory system.
4. Plugin tool handlers **must** be thread-safe (ledger writes). Concurrent tool pool is the default.
5. Do not hook-police `memory` / `todo` / `delegate_task` / `session_search`. Honcho is `memory.provider`. Do not also write a parallel `MEMORY.md` personality.
6. Subagents lose SOUL. If this profile ever delegates, the plugin + skills must carry the workflow, not SOUL alone.
7. This repo’s root `AGENTS.md` is Cursor workflow, not Hermes runtime, unless the agent cwd actually has that file (and no `.hermes.md` / `HERMES.md`). Do not rely on it at runtime.
8. Ledger lives in `<HERMES_HOME>/plugin-data/research-bot/source-ledger.json`. It must survive compression child-session lineage. Do not key it only to a discarded session id without a fallback.
9. These locks cite the official URLs above. Do not invent knobs from training data.

---

## Source C — Adding Tools (built-in core only)

https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools

- **Warning on the page:** this guide is for **built-in** core tools in `tools/` + `toolsets.py` only. Custom / personal / project tools **must** use the plugin route. Do not add research-bot tools to Hermes core.
- Skill vs tool: skill = instructions + shell + existing tools (arXiv, git, Docker, PDF). Tool = API keys, custom processing, binary, streaming.
- Handler rules (danger box): MUST return `json.dumps` string, never a dict. Errors MUST be `{"error": "..."}`, never raise. `handler(args: dict, **kwargs)`. `check_fn` False = silently excluded from tool definitions.
- Schema example is **flat**: `{name, description, parameters:{type:object, properties, required}}`. Use that, not the CONTRIBUTING `{type:function,function:{...}}` wrapper unless Context7 shows plugins accept both.
- `is_async=True` if the handler is async; never `asyncio.run` yourself.
- Per-session state: `task_id = kwargs.get("task_id")`.
- Agent-loop intercepted tools (`todo`, `memory`, `session_search`, `delegate_task`): schemas live in the registry but `dispatch()` returns a fallback error if intercept is bypassed. Do not hook-police them.

---

## Source D — Native plugins

https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

- Native plugin = `plugin.yaml` + `__init__.py` `register(ctx)`. Discovery: `~/.hermes/plugins/`, `./.hermes/plugins/`, pip entry points. Layout: flat `~/.hermes/plugins/<name>/` or **one** category level. Deeper ignored. Missing `__init__.py` or not in `plugins.enabled` = skip.
- Memory providers are `kind: exclusive` via `memory.provider`, **not** `plugins.enabled`. Do not write a second memory plugin.
- `register()` once at startup. Crash disables only that plugin.
- `ctx.register_tool` / `register_hook` / `register_middleware` / `register_command` / `register_cli_command` / `dispatch_tool` / `call_mcp` / `get_config` / `set_config` / `ctx.state` / `ctx.profile_name` / `has_capability` / `register_skill`.
- Settings: `plugins.entries.<id>.settings` via `ctx.get_config` (plugin-relative only). Runtime: `ctx.state` (atomic, concurrent-safe, 10 MiB) and `plugin_data_dir("research-bot")` / `plugin_db` (WAL). **Never** write state into the plugin install tree.
- Manifest v2 optional: `config_schema`, `requires_plugins` (advisory, load-order only), `python_dependencies` (never auto-installed).
- Capabilities (`tools.override`, `llm.*_override`) are consent, not a sandbox. This profile does **not** override builtins.
- Plugin-bundled skills via `ctx.register_skill` are read-only, namespaced `plugin:skill`, **not** in `<available_skills>`. Primary research skills stay in profile `skills/`.
- `pre_llm_call` injects onto the **user** message; 10k char spill to `hook_outputs`. Multiple plugins concatenate, discovery order alphabetical by directory name. Keep research contract + ledger digest under the cap.
- `post_tool_call` fires for **all** tools, not just ours.
- Middleware `tool_request` rewrites args **before** hooks/guardrails/approvals. Return `None` if no change.
- Thread pool: use `plugins.plugin_utils.lazy_singleton` / `SingletonSlot`. Do not hand-roll a global `_client`.
- `ctx._cli_ref` is `None` in gateway, `hermes chat -q`, and kanban workers. Use `ctx.profile_name` and `ctx.dispatch_tool`.
- `check_fn` hides a tool from the model.
- Doctor: `hermes plugins doctor <path> --ci` (local, not CI).
- Portable Agent Plugins v1 (`plugin.json` + skills + `mcp.json`) is a compatibility subset, **not** this profile’s path.

---

## Locked consequences (native plugin path)

1. research-bot is a **native general** plugin (`plugin.yaml` + `register(ctx)`). Never a core `tools/` patch. Never a memory-provider plugin.
2. Required files: `plugin.yaml`, `__init__.py`, `schemas.py`, `tools.py`. Schema descriptions must say **when to call** `resolve_library` / `docs_query` / `source_ledger_cite` (cite).
3. Handlers: JSON string, `**kwargs`, never raise, `task_id` from kwargs, thread-safe ledger via `plugin_data_dir` or `ctx.state`.
4. `plugins.enabled: [research-bot]`. Honcho stays `memory.provider`.
5. `distribution_owned` includes `plugins/` so profile install copies into the profile `HERMES_HOME` plugins tree (flat name `research-bot`).
6. Do not `register_skill` the primary library. Optional companions only.
7. `pre_llm_call` under 10k. Ledger survives compression lineage.
8. Cite the official URLs in this file. Do not invent knobs from training data.
