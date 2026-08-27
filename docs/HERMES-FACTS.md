# Hermes facts for HDR v2

**Probe date:** 2026-08-27.  
**Spec:** `docs/HDR-SPEC.md` (commit `3057932`).  
**Context7 library:** `/nousresearch/hermes-agent` (listed versions `v2026.4.8`, `v2026.4.16`, `v2026.6.5`).  
**Then:** official pages in spec §12.  
**Rule:** every `[DOC]` and `[UNV]` in the spec has a URL, a quoted knob name, and a version note. Every `[UNV]` is `[DOC]` or **removed**. Do not invent a replacement knob.

Version note: official pages do not stamp a Hermes release on each knob. Official `hermes_requires` examples use `>=0.12.0` and `>=0.13.0`. This file uses **live docs 2026-08-27** plus the Context7 library versions above.

---

## STOP — official page disagrees with the spec

The spec §4.2 bundle and P1 acceptance list toolset `moa`.

Official Mixture of Agents page:

> MoA is no longer listed under `hermes tools`; there is no `moa` toolset to enable.

URL: https://hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents  
Knob: **no `moa` toolset**. MoA is provider `moa`. Slash command `/moa`. Config block `moa.presets`.  
Version: live docs 2026-08-27.

Spec §7.4 also says run `mixture_of_agents` as if it were a tool. Official has no such tool.

**Action:** remove `moa` from `custom_toolsets.research`. Do not invent a replacement toolset. MoA verification, if used, is a model-provider selection (`/model … --provider moa` or `/moa`), not a toolset. P1 `/tools list` cannot show `moa`.

No other official page required a stop. Other mismatches below are recorded and resolved without a new knob.

---

## [UNV] register — resolved or removed

| Spec [UNV] | Outcome | Why |
| --- | --- | --- |
| `browser.cdp_url: "${env:HERMES_CDP_URL}"` | **[DOC]** for `browser.cdp_url`. Env name is ours. | Official key is `browser.cdp_url`. `${env:VAR}` interpolation is official in `config.yaml`. `HERMES_CDP_URL` is not an official Hermes env name. Keep as deploy-host env. |
| `openalex` / `pubmed` / `wayback` as Hermes MCP servers | **Removed** as first-party Hermes servers | No official Hermes page names these servers. `mcp.json` may list any HTTP/stdio server. Facades use HTTP (Crossref, Unpaywall, Wayback CDX) unless the host adds a server. Do not invent official URLs. |
| `hermes_requires: ">=0.14.0"` | **Removed** | Official examples are `>=0.12.0` and `>=0.13.0`. No page dates `register_system_prompt_section` or `proactive_prune_tokens` to 0.14.0. P1 uses `>=0.13.0` (documented example), not an invented 0.14.0. |
| `pre_tool_call` can block `delegate_task` | **[DOC]** | Official: use `pre_tool_call` to block `delegate_task`. |
| Children share `HERMES_HOME` | **[DOC]** for profile-home paths. Transcript backstop stays. | `plugin-data/` is `<HERMES_HOME>/plugin-data/`. Live transcripts are `<hermes_home>/cache/delegation/live/…`. Children of a profile session use that home. No sentence says “child process getenv HERMES_HOME equals parent.” Keep the transcript grep. |
| `ctx.llm` for a citation pass | **[DOC]** | Official Plugin LLM Access. Out of band. Trust-gated. |
| CDP / Camofox | **[DOC]** | Official `browser.cdp_url` and `browser.camofox`. |

---

## 1. Prompt assembly and SOUL

### SOUL is identity. First slot. No tools, paths, or MCP

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- **Quote:** “`SOUL.md` lives at `~/.hermes/SOUL.md` and serves as the agent's identity — the very first section of the system prompt.”
- **Quote:** “When `skip_context_files` is set (e.g., subagent delegation), SOUL.md is not loaded and the hardcoded `DEFAULT_AGENT_IDENTITY` is used instead.”
- **Version:** live docs 2026-08-27.

Also: https://hermes-agent.nousresearch.com/docs/guides/use-soul-with-hermes (SOUL is primary identity).

### Cached system is built once. Three tiers

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- **Quote:** “The cached system prompt is assembled as three ordered tiers … `stable` → `context` → `volatile`.”
- **Version:** live docs 2026-08-27.

### `pre_llm_call` is API-call-time on the user message

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- **Quote:** “`pre_llm_call` plugin context also lands in this API-call-time path: it is appended to the current turn's user message, not written into the cached system prompt.”
- **Version:** live docs 2026-08-27.

### Hook context spill cap 10 000 chars

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- **Quote:** “Per-hook context is capped at `10,000` characters by default.”
- **Knob:** `hooks.output_spill.max_chars` (default 10000).
- **Version:** live docs 2026-08-27.

HDR volatile digest is a plugin choice of 1 200 chars. That is `[INF]`, under the official 10k cap.

---

## 2. `register_system_prompt_section`

- **URL:** https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- **Knob:** `ctx.register_system_prompt_section`
- **Quote:** “`after_memory` is the only placement anchor.”
- **Quote:** “A callable receives a read-only mapping with `session_id`, `model`, `provider`, `platform`, `profile_name`, and `cwd`. It runs once for a new session. Its rendered bytes are frozen on compression …”
- **Quote:** “`max_chars` is capped at 4,000 characters. All plugin sections together, including their audit headings, are capped at 8,000 characters and 32 sections.”
- **Version:** live docs 2026-08-27. Context7 `/nousresearch/hermes-agent`.

This resolves spec G06 `[DOC]`.

---

## 3. Hooks used by HDR

Catalog URL: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks  
VALID_HOOKS also listed in Context7 from `hermes_cli/plugins.py`.  
Version: live docs 2026-08-27.

| Knob | Category | Official quote |
| --- | --- | --- |
| `pre_tool_call` | Directive | “first valid `block` or `approve` directive wins, and `modify` returns are shallow-merged into the tool arguments.” |
| `post_tool_call` | Observer | “After blocked, error, or successful result; return ignored.” |
| `transform_tool_result` | Transform | “After `post_tool_call`, before conversation append; first string replaces the result.” |
| `transform_terminal_output` | Transform | “first string replaces output.” |
| `pre_llm_call` | Directive | “all valid string/`{"context": ...}` returns are joined and injected into the user message.” |
| `transform_llm_output` | Transform | “first non-empty string replaces the response.” |
| `pre_verify` | Directive | “Fires … only when the agent edited code this turn and at least one `pre_verify` hook is registered.” |
| `pre_api_request` | Observer | payload includes `approx_input_tokens`. “return ignored.” |
| `post_api_request` | Observer | payload includes `usage`. “return ignored.” |
| `api_request_error` | Observer | “On each failed provider attempt; return ignored.” |
| `on_session_start` | Observer | “First turn of a new session; return ignored.” |
| `on_session_end` / `on_session_finalize` | Observer | catalog entries exist. |
| `on_session_reset` | Observer | in `VALID_HOOKS`. |
| `subagent_start` | Observer | “cannot block execution; use `pre_tool_call` to block delegation.” |
| `subagent_stop` | Observer | “Fires once per child agent after `delegate_task` finishes.” |
| `plugins.stream_reasoning_deltas` | Config | reasoning deltas “require the `plugins.stream_reasoning_deltas` opt-in.” |

### `pre_verify` does not fire for markdown-only turns

- **URL:** https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- **Quote:** “only when the agent edited code this turn”
- **Version:** live docs 2026-08-27.

This is spec §13 `[DOC]`. Citation Gate stays in `pre_tool_call`.

### Fail-open vs fail-closed on hook timeout

- **URL:** https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- **Quote:** “Timed-out or still-running `pre_tool_call` callbacks fail closed (block the tool); other bounded hooks fail open (skip).”
- **Version:** live docs 2026-08-27.

`transform_tool_result` must fail open in plugin code (return `None`). Official timeout path already skips non-`pre_tool_call` hooks.

---

## 4. Agent loop

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- **Quote:** “Multiple tool calls → executed concurrently via `ThreadPoolExecutor`.”
- **Quote:** intercepted before registry: `todo`, `memory`, `session_search`, `delegate_task`.
- **Quote:** “Preflight (before API call): If conversation exceeds 50% of model's context window.”
- **Quote:** “Memory is flushed to disk first … The last N messages are preserved intact (`compression.protect_last_n`, default: 20) … Tool call/result message pairs are kept together (never split).”
- **Overlap:** this page still says “A new session lineage ID is generated (compression creates a ‘child’ session).” The compression page says `in_place: true` is default. Spec G22 already chose the compression page. See §5.
- **Version:** live docs 2026-08-27.

---

## 5. Compression and caching

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching
- **Also:** https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- **Version:** live docs 2026-08-27.

| Knob | Official quote / default |
| --- | --- |
| `compression.enabled` | default true |
| `compression.threshold` | default 0.50 |
| `compression.threshold_tokens` | “Absolute token cap (optional) — takes lower of ratio vs absolute.” Default `null`. |
| `compression.tail_mode` | “`lean` (default) … ~3x fewer retained tokens after compaction” or `legacy`. |
| `compression.protect_last_n` | default 20 |
| `compression.protect_first_n` | “Non-system head messages pinned across every compaction. Default `3`.” Spec value 2 is allowed. |
| `compression.in_place` | “Compact on the same session id, no rotation (default: true).” “pre-compaction turns are soft-archived under the same id.” |
| `compression.idle_compact_after_seconds` | default 0. Example `1800`. |
| `compression.proactive_prune_tokens` | “default `0` = off; try `48000` to enable.” |
| `compression.proactive_prune_min_result_chars` | default 8000 |
| `compression.proactive_prune_min_reclaim_tokens` | default 4096 |
| `prompt_caching.cache_ttl` | “Only the two Anthropic-supported tiers (`"5m"`, `"1h"`) are honored.” |
| `auxiliary.compression` | model / provider / `reasoning_effort` for the summarizer |

**Forked-children cache claim:** official says cache TTL is Anthropic 5m/1h. Official MoA page says the main conversation cache is not broken by MoA. Official does **not** say `cache_ttl` is reused for forked `delegate_task` children as a separate guarantee. Treat “across forked children” as `[INF]` unless a later page quotes it.

Oversized tool results persist in the session store after prune (“Full outputs stay recoverable from the session store”). That is the official spill the Evidence Bus sits beside.

---

## 6. Agent budget and tool output

URL: https://hermes-agent.nousresearch.com/docs/user-guide/configuration  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `agent.max_turns` | “unlimited by default” — `"none"` is a documented spelling. |
| `agent.run_budget_seconds` | “Optional; unset/null = feature fully off (default).” “Wrap-up notice at 80%.” One-time. |
| `agent.disabled_toolsets` | “suppress specific toolsets across the CLI and every gateway platform.” |
| `agent.verify_on_stop` | exists; spec leaves it false. |
| `file_read_max_chars` | default 100000. Spec 150000 is allowed. |
| `context_file_max_chars` | default scales; explicit value wins. |
| `tool_budget.mcp_result_size_chars` | “per-result spillover threshold for mcp_* tools” (example 50000). Spec 30000 is allowed. |
| `tool_output.max_bytes` / `max_lines` / `max_line_length` | documented under configuration / terminal output caps. |

---

## 7. Terminal, Docker, skills env

URL: https://hermes-agent.nousresearch.com/docs/user-guide/configuration  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `terminal.backend` | `local \| docker \| ssh \| modal \| daytona \| vercel_sandbox \| singularity` |
| `terminal.backend: docker` | documented, with `docker_image`, `docker_network`, `container_persistent`, `container_memory`, `timeout` |
| `terminal.env_passthrough` | “Env var names to forward to sandboxed execution (terminal + execute_code)” |
| `terminal.cwd` | “CLI always uses launch dir” |
| `skills.inline_shell` | creating-skills: snippets in SKILL.md; `inline_shell: true` runs them on the host |
| `skills.write_approval` / `guard_agent_created` | configuration / skills pages |

`${env:VAR}` in `config.yaml` and `mcp_servers`: “Cursor-style SecretRef syntax is also accepted: `${env:VAR_NAME}` resolves exactly like `${VAR_NAME}`.”

---

## 8. Web search and extract

URL: https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `web.search_backend` / `web.extract_backend` | per-capability split is official |
| `SEARXNG_URL` | official env. Self-hosted: “With Docker, your own instance has no rate limits.” |
| `FIRECRAWL_API_URL` | “When `FIRECRAWL_API_URL` is set, the API key is optional (disable server auth with `USE_DB_AUTHENTICATION=false`).” |
| `web.keyless_fallback` | official default on. “Set `web.keyless_fallback: false` to turn the tier off.” Spec v2 sets **true**. |
| `web.keyless_rescue` | “Disable with `web.keyless_rescue: false` (also off whenever `keyless_fallback` is off).” Spec v2 sets **true**. |

---

## 9. Browser and vision

URL: https://hermes-agent.nousresearch.com/docs/user-guide/configuration  
Also toolsets from Context7 `toolsets.py`.  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `browser.cdp_url` | “Optional CDP override — when set, Hermes attaches directly to your own Chromium-family browser.” |
| `browser.camofox` | `managed_persistence`, `user_id`, `session_key`, `adopt_existing_tab` |
| toolset `browser` | `browser_navigate`, `browser_snapshot`, `browser_vision`, `browser_cdp`, … |
| toolset `vision` | `vision_analyze` |
| toolset `x_search` | “Off by default; enable in `hermes tools`.” Not in the HDR bundle. |

`HERMES_CDP_URL` is a host env name we pass into `browser.cdp_url` via `${env:HERMES_CDP_URL}`. It is not a Hermes-defined env.

---

## 10. Toolsets in the HDR bundle

URL: https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference  
Context7: `toolsets.py` `TOOLSETS` dict.  
Version: live docs 2026-08-27.

Official built-in ids used by the spec bundle:

`web`, `browser`, `vision`, `file`, `terminal`, `code_execution`, `skills`, `memory`, `session_search`, `todo`, `clarify`, `delegation`, `cronjob`.

`hdr` is this plugin’s toolset (plugin-registered). Official: every tool belongs to one toolset.

**`moa` is not a toolset.** Removed. See STOP.

**`kanban`:** “strictly opt-in, requiring explicit listing rather than being enabled by wildcards.” Spec leaves it out. `[DOC]`.

`agent.disabled_toolsets` is the global kill switch. `[DOC]`. Do not set it in this profile.

---

## 11. Delegation

URL: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation  
Also: https://hermes-agent.nousresearch.com/docs/user-guide/configuration  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `delegation.model` / `provider` | “empty = inherit parent” |
| `delegation.max_concurrent_children` | default 3. “no hard ceiling.” |
| `delegation.max_iterations` | default 50 |
| `delegation.max_spawn_depth` | “1-3, clamped. 1 = flat (default). 2 = orchestrator children can spawn leaf grandchildren.” |
| `delegation.orchestrator_enabled` | default true |
| `delegation.child_timeout_seconds` | default 0 (none) in `config_defaults.py` |
| `delegation.worktree_isolation` | default false |
| inherit toolsets | “Subagents inherit their parent's enabled toolsets … a model cannot grant a child capabilities the parent lacks.” |
| leaf blocks | “Leaf subagents cannot call: `delegate_task`, `clarify`, `memory`, `send_message`, `cronjob`.” |
| `execute_code` | “Both roles retain `execute_code`.” Resolves v1 G23. |
| skip SOUL | “SOUL.md is excluded.” |
| `delegate_task(background=true)` | “Background delegations (`delegate_task(background=true)`) are watched by a progress-based stall monitor.” Top-level calls “run in the background automatically” where the session can deliver later. |
| `{"action":"steer", …}` | official control action. |
| live transcripts | `<hermes_home>/cache/delegation/live/<delegation_id>/task-<n>.log` |
| `/review` | “full-privilege background subagent.” Pin `auxiliary.review`. |

`pre_tool_call` **can** block `delegate_task`:

> To block delegation before a child is built, use `pre_tool_call` to block the `delegate_task` tool call.

URL: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks

---

## 12. Subagent lifecycle API (plugin host)

- **URL:** https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api
- **Knob:** `ctx.subagent_lifecycle`
- **Quote:** “Launching outside an active agent turn fails closed with `No active Hermes parent session`.”
- **Quote:** “Use `allowed_toolsets` to narrow a child.” Per-tool blocks, workdir overrides, and per-launch timeouts are rejected.
- **Version:** live docs 2026-08-27.

This does not replace `delegate_task`.

---

## 13. Plugin contract

URL: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins  
Also: https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| handler | “Return: Always a JSON string.” “Never raise.” “Accept `**kwargs`.” |
| `plugin.yaml` + `register(ctx)` | native general plugin path |
| `plugin.json` | Portable Agent Plugins v1 — not this profile’s path |
| `plugin-data/` | “state is plugin-owned runtime data under `<HERMES_HOME>/plugin-data/`.” |
| `plugin_data_dir("my-plugin")` | “`<hermes home>/plugin-data/<name>/` — created on first use” |
| `ctx.call_mcp` | join to MCP. Envelope `{ok, result}` / `{ok, error}` (playbook + adding-tools). |
| `ctx.llm` | https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access — “the supported way for a plugin to make an LLM call.” |
| `plugins.enabled` | opt-in. `plugins.disabled` always wins (user plugins page). |
| `plugins.entries.<id>.mcp_allowlist` | default-off; no wildcards (user plugins page / playbook). |

---

## 14. Skills

URL: https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills  
Also: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `metadata.hermes.requires_toolsets` | nested under `metadata.hermes`. “Show ONLY when these toolsets are available.” |
| `metadata.hermes.requires_tools` | same. If any listed capability is missing, the skill is hidden. |
| `metadata.hermes.fallback_for_tools` | “Show ONLY when these specific tools are unavailable.” |
| `${HERMES_SKILL_DIR}` | “`node ${HERMES_SKILL_DIR}/scripts/analyse.js`” — absolute skill dir. |
| `${HERMES_SESSION_ID}` | creating-skills / work-with-skills (session scratch). |
| `required_environment_variables` | “automatically passed through to `execute_code` and `terminal` sandboxes — including remote backends like Docker and Modal.” |
| `metadata.hermes.blueprint` | “Hermes registers it as a **suggested cron job** rather than scheduling it.” |
| `skills.inline_shell: false` | keep off so SKILL.md snippets do not run on the host. |

v1 flat top-level `requires_*` is the wrong shape (G16). Use nested `metadata.hermes`.

---

## 15. MCP

URL: https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `mcp_servers.<name>.url` + `headers` | HTTP servers |
| `${env:VAR}` | official in server entries |
| `tools.include` | “If `include` is set, only those server-native MCP tools are registered.” Official does **not** say empty `[]` is unset. **Omit `include`.** Do not write `include: []`. |
| `enabled: false` | “no connection attempt … no tool registration.” Breaks `ctx.call_mcp`. |
| `tools.resources` / `tools.prompts` | bool-like utility tools |

No official page names MCP servers `openalex`, `pubmed`, or `wayback`. Removed as Hermes-owned servers. Context7 stays as the one first-party remote we already ship.

---

## 16. Distribution and install

URL: https://hermes-agent.nousresearch.com/docs/user-guide/features/profile-distributions  
Also: https://hermes-agent.nousresearch.com/docs/reference/profile-commands  
Version: live docs 2026-08-27.

| Knob | Official quote |
| --- | --- |
| `distribution.yaml` at the distribution root | “`hermes profile install` … from a git URL or local directory containing a distribution.yaml manifest.” |
| GitHub-URL install | looks at **repo-root** `distribution.yaml`. Official examples are **one** distribution per repo. No official multi-profile index schema. |
| `DEFAULT_DIST_OWNED` | `SOUL.md`, `config.yaml`, `mcp.json`, `skills`, `cron`, `distribution.yaml`. **`plugins` is not in the default.** |
| `distribution_owned` | “if omitted, defaults … apply.” Setting the list **replaces** the default. Must list `plugins` if we ship one. |
| `hermes_requires` | official examples `>=0.12.0` and `>=0.13.0`. **0.14.0 removed.** |
| `config.yaml` on update | preserved unless `--force-config`. |
| `plugin-data/` | not in the install tree. |

**Repo-root index:** official GitHub-URL install copies the **repo root** as the payload. A root `distribution.yaml` without the profile files at root would install an empty shell. Official has no `profiles: []` index. Do not invent one.

P1 keeps path install: `hermes profile install ./agents/research-bot`. The root README states the official GitHub-URL limit (one distribution per repo). That removes an invented multi-profile index. It does not add a knob.

---

## 17. Memory (Honcho)

URL: https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin  
Also: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers  
Version: live docs 2026-08-27.

| Knob | Fact |
| --- | --- |
| `memory.provider: honcho` | official provider id. **Not** in `plugins.enabled`. |
| `memory.memory_char_limit` / `user_char_limit` | official memory size knobs (configuration). |
| `pinUserPeer` | gateway-only. CLI no-op. Keep in the example. Do not build on it. |
| `memory` tool | intercepted before the registry. A `pre_tool_call` block is ineffective. Observer log only. |

---

## 18. Plugin LLM and auxiliary review

| Knob | URL | Quote |
| --- | --- | --- |
| `ctx.llm` | https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access | “`ctx.llm` is the supported way for a plugin to make an LLM call.” |
| `auxiliary.review` | configuration + delegation `/review` | reviewer model pin |
| `auxiliary.vision` | configuration | vision model |
| `auxiliary.compression` | configuration / compression page | cheap summarizer |
| MoA reasoning | configuration | “reasoning depth for Mixture-of-Agents is configured **per slot** in the MoA preset (`moa.presets.<name>.reference_models[].reasoning_effort` / `aggregator.reasoning_effort`), not on the `moa_reference`/`moa_aggregator` auxiliary blocks.” |

---

## 19. Handler and tool-call contract (unchanged)

URL: https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools  
Version: live docs 2026-08-27.

1. `handler(args, **kwargs)`  
2. Return `json.dumps` string. Never a dict.  
3. Errors `{"error": "..."}`.  
4. Never raise.  
5. `task_id = kwargs.get("task_id")`.

---

## 20. Spec `[DOC]` checklist

Every `[DOC]` tag in `HDR-SPEC.md` maps to a row above. Short index:

| Spec claim | Status |
| --- | --- |
| `transform_tool_result` intercepts retrieval results | DOC — hooks |
| Hermes spills oversized results to disk | DOC — prune + session store |
| `pre_tool_call` / `pre_api_request` / `post_api_request` | DOC — hooks |
| `agent.run_budget_seconds` 80% wrap-up | DOC — configuration |
| SOUL identity only | DOC — prompt-assembly |
| `delegation.*` knobs | DOC — configuration + delegation |
| `auxiliary.compression.reasoning_effort` | DOC — configuration |
| `auxiliary.review` | DOC — `/review` |
| compression knobs including `proactive_prune_tokens` | DOC — configuration + compression |
| `tool_budget.mcp_result_size_chars` | DOC — configuration |
| `prompt_caching.cache_ttl` | DOC — `"5m"` / `"1h"` only |
| `agent.max_turns: none` | DOC — configuration |
| `terminal.backend: docker` | DOC — configuration |
| `env_passthrough` / skill env passthrough | DOC |
| `code_execution` toolset | DOC — toolsets |
| kanban not in `all`/`*` | DOC — toolsets |
| `agent.disabled_toolsets` | DOC |
| `plugins` must be in `distribution_owned` | DOC — DEFAULT_DIST_OWNED |
| thread pool for registry tools | DOC — agent-loop |
| `memory` intercepted before registry | DOC — agent-loop |
| prompt section frozen on compression | DOC — hooks |
| 4k / 8k section caps | DOC — hooks |
| `modify` shallow-merge | DOC — hooks |
| `transform_llm_output` first non-empty string | DOC — hooks |
| `pre_verify` code-only | DOC — hooks |
| nested `metadata.hermes` | DOC — creating-skills |
| `fallback_for_tools` | DOC — creating-skills |
| `${HERMES_SKILL_DIR}` | DOC — creating-skills |
| `required_environment_variables` auto-pass | DOC — creating-skills |
| `inline_shell` host execution | DOC — creating-skills |
| `blueprint:` suggested cron | DOC — creating-skills |
| children inherit toolsets, cannot widen | DOC — delegation |
| both roles keep `execute_code` | DOC — delegation |
| children skip SOUL | DOC — delegation + prompt-assembly |
| live transcript path | DOC — delegation |
| `delegate_task(background=true)` | DOC — delegation |
| `{"action":"steer"}` | DOC — delegation |
| MoA reasoning per slot | DOC — configuration + MoA page |
| SearXNG self-host no cloud quota | DOC — web-search |
| `FIRECRAWL_API_URL` makes key optional | DOC — web-search |
| `in_place` default + soft-archive | DOC — compression (overrides agent-loop lineage sentence) |

---

## 21. What code may depend on

Allowed: every `[DOC]` row above.

Removed before code depends on them:

1. Toolset `moa` (official: no such toolset).  
2. First-party MCP servers named `openalex`, `pubmed`, `wayback`.  
3. `hermes_requires: ">=0.14.0"`.  
4. A repo-root multi-profile `distribution.yaml` schema that official docs do not define.

Host env (not Hermes knobs): `SEARXNG_URL`, `FIRECRAWL_API_URL`, `CONTEXT7_API_KEY`, `HERMES_CDP_URL`, `UNPAYWALL_EMAIL`, `CROSSREF_MAILTO`, `SEMANTIC_SCHOLAR_API_KEY`.

---

## 22. Official URL list (probe set)

- https://hermes-agent.nousresearch.com/docs/user-guide/configuration  
- https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation  
- https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills  
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins  
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools  
- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop  
- https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly  
- https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/profile-distributions  
- https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin  
- https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api  
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access  
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference  
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills  
- https://hermes-agent.nousresearch.com/docs/guides/use-soul-with-hermes  
