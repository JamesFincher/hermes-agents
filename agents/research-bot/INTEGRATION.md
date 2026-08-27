# research-bot instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)

This file is the join map for **this profile only**. Extracted from the official pages James shared — not from training data.

| Official page | URL |
| --- | --- |
| Agent Loop Internals | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| Prompt Assembly | https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly |

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
9. These locks cite both official URLs above. Do not invent knobs from training data.
