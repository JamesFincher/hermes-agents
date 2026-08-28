# inception spec

**Verdict.** Ship a second shelf item that authors isolated profiles by running `docs/PROFILE-PLAYBOOK.md`. It is a factory, not a shared runtime.

**Canvas:** [`inception-canvas.md`](inception-canvas.md)

Every platform claim is tagged. Code does not depend on `[UNV]`.

## Gap register

New profile. No prior `agents/inception/`. Gaps are the library rules this spec must not break.

| id | gap | severity | evidence | fix |
| --- | --- | --- | --- | --- |
| G1 | Next profile must start empty of `hdr` | S1 | playbook law 1 | `plugins.enabled: [inception]` only |
| G2 | Validator schemas check was hdr-named | S2 | `validate_factory.py` | hdr-only needles; inception lists its own tools |
| G3 | Live CLI | S2 | this VM | Document UNPROVEN. Do not invent `plugins doctor`. |

## Incumbent mechanism map

See canvas §3. Custom work is the probe ledger, the scaffold writer, and the isolation fence. Hermes has no official multi-profile GitHub index `[UNV]`.

## Load-bearing inventions

1. Factory ledger in `plugin-data/inception/` (not memory).
2. Deterministic scaffold that `validate_factory.py` accepts.
3. Policy fence on reserved names and secret files.
4. Docs facades that refuse a card without an openable URL.

## Surface-by-surface

### SOUL

Identity. Librarian voice. No paths. No MCP names. No tool procedures.

### config.yaml

See `agents/inception/config.yaml`. Bundle `factory`. Locked gather. Local terminal. Fan-out off.

### MCP

`context7` only. `mcp_allowlist: [context7]`. Omit `tools.include`. Do not set `enabled: false`. [DOC] https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference

### Plugin

`agents/inception/plugins/inception/`. `register(ctx)` registers five tools and seven hooks.

### Tools

Exact names: `docs_resolve`, `docs_ask`, `probe_knob`, `scaffold_profile`, `check_profile`. Flat schemas in `schemas.py`.

### Skills

`author-profile` (steps 0-4 then 5-10), `probe-knob`, `review-profile` (§10). Nested `metadata.hermes`. No `CONTEXT7_API_KEY` on a skill.

### Delegation

Rejected. Written down.

### Memory

Settled paragraph in `INTEGRATION.md`. `aiPeer: hermes.inception`.

### Distribution + eval

`hermes_requires: ">=0.13.0"`. Path install. Ten frozen tasks. Unit tests are the CI gates.

## Knob sweep

| Knob | Decision | Reason |
| --- | --- | --- |
| `model.default` | default | Operator pins on the host. Do not invent a model id. |
| `delegation.model` / `provider` / `base_url` | reject | Fan-out is off. |
| `auxiliary.compression.model` | default | Inherit. |
| `auxiliary.compression.reasoning_effort` | accept `low` | Cheap summarizer. [DOC] configuration |
| `auxiliary.vision.*` | reject | No vision toolset. |
| `auxiliary.approval.*` | default | Unused. |
| `auxiliary.review.model` | default | Empty object. Operator may pin. |
| `auxiliary.title_generation.enabled` | accept `false` | Factory runs do not need titles. |
| `auxiliary.*.fallback_chain` | default | Not required. |
| `auxiliary.compression.max_concurrency` | accept `1` | Single-thread factory. |
| `fallback_providers` | default | Host concern. |
| `credential_pool_strategies` | default | Host concern. |
| `prompt_caching.cache_ttl` | accept `1h` | Official Anthropic tier. [DOC] |
| `compression.threshold` | accept `0.55` | Slightly later than default 0.50. |
| `threshold_tokens` | accept `120000` | Docs payloads. |
| `tail_mode` | accept `lean` | Official default path. [DOC] |
| `protect_last_n` | accept `12` | Keep the last factory steps. |
| `protect_first_n` | accept `2` | Allowed. [DOC] |
| `in_place` | accept `true` | Official default. [DOC] |
| `idle_compact_after_seconds` | accept `1800` | Example on the compression page. |
| `proactive_prune_tokens` | accept `32000` | Ops archetype. [DOC] |
| `proactive_prune_min_result_chars` | accept `4000` | Companion. |
| `proactive_prune_min_reclaim_tokens` | accept `4096` | Official default companion. |
| `tool_output.max_bytes` | accept `40000` | Bound dumps. |
| `tool_output.max_lines` | accept `800` | Bound dumps. |
| `tool_output.max_line_length` | accept `1200` | Bound dumps. |
| `tool_budget.mcp_result_size_chars` | accept `30000` | Distil sits beside the official spill. |
| `file_read_max_chars` | accept `100000` | Official default. |
| `context_file_max_chars` | accept `20000` | Project file cap. |
| `context.engine` | default | Built-in compressor. Do not write a second engine. [DOC] |
| `agent.max_turns` | accept `none` | Official spelling. [DOC] |
| `agent.run_budget_seconds` | accept `1800` | Factory jobs need a wall clock. |
| `agent.api_max_retries` | accept `2` | Short retry. |
| `agent.verify_on_stop` | accept `false` | `check_profile` is the gate. |
| `verify_guidance` / `max_verify_nudges` | default | Unused. |
| `agent.coding_instructions` | accept `""` | Not a coding agent. |
| `goals.max_turns` | default | No goals workflow. [UNV] if pages disagree; code does not read it. |
| `agent.session_stall_timeout` | accept `300` | Recover hung MCP. |
| `delegation.max_concurrent_children` | accept `1` | Written default. Bundle omits `delegation`. |
| `max_iterations` | accept `20` | Written default. |
| `max_spawn_depth` | accept `1` | Flat. |
| `orchestrator_enabled` | accept `false` | No children. |
| `child_timeout_seconds` | accept `0` | Official none. |
| `worktree_isolation` | accept `false` | Official default. |
| `surface_child_process_notifications` | accept `false` | No children. |
| `terminal.backend` | accept `local` | Scaffold must write the checkout. [INF] |
| `docker_*` / `container_*` | reject | Local backend. |
| `home_mode` | default | Not needed. |
| `env_passthrough` | accept `[]` | No extra host env in the shell. |
| `worktree` | default | Unused. |
| `custom_toolsets.factory` | accept | `web`, `file`, `terminal`, `skills`, `memory`, `session_search`, `todo`, `clarify`, `inception`. |
| `toolsets` | accept `[factory]` | Enable the bundle. |
| `agent.disabled_toolsets` | reject | Do not set a global kill switch. |
| per-tool disables | default | None. |
| `mcp_servers` + `mcp_allowlist` | accept `context7` | Facade path. |
| `plugins.enabled` | accept `[inception]` | This profile only. |
| `plugins.stream_reasoning_deltas` | accept `false` | Not required. |
| `memory.provider` | accept `honcho` | Settled. [DOC] |
| memory limits | accept | Bound injection. |
| `memory.write_approval` | accept `false` | Factory may write memory. |
| `skills.inline_shell` | accept `false` | Do not run SKILL.md snippets on the host. [DOC] |
| `skills.write_approval` | accept `false` | Skills may write. |
| `skills.guard_agent_created` | accept `true` | Official guard. |
| `skills.config.*` | reject | Do not duplicate plugin settings. |
| `moa` toolset | reject | Official STOP. MoA is a provider. |
| `browser` / `vision` / `cronjob` / `code_execution` / `delegation` | reject | Not in the factory bundle. |

## Hook table

| Hook | Category | Fail | Role |
| --- | --- | --- | --- |
| `on_session_start` | Observer | open | Init store |
| `pre_llm_call` | Directive | open | Digest ≤800 |
| `pre_tool_call` | Policy | closed + why | Fence |
| `transform_tool_result` | Transform | open | Distil |
| `transform_llm_output` | Transform | open | Footer |
| `pre_api_request` | Observer | open | Governor count |
| `post_api_request` | Observer | open | No-op |

## Data schema

`factory.json` `version: 1`. Lists: `probes`, `cards`, `scaffolds`, `checks`, `audit`. Object: `governor`.

## Delegation topology

None.

## Token economics

Measured on fixture handler runs, not live Hermes. See README. Live cost is `[UNV]`.

## Failure ladder

Canvas §10. Fixture: Context7 down → `docs_ask` returns `{"error":…}` and stores no card.

## Eval

`agents/inception/evals/`. Ten tasks. Two adversarial. CI: `python -m unittest discover -s tests -v`.

## Phased build

P1 package files. P2 store. P3 hooks. P4 tools + section. P5 skills. P6 eval + docs.

## Sources

Context7 `/nousresearch/hermes-agent` and `/plastic-labs/honcho`. Playbook. `docs/HERMES-FACTS.md`. Official URLs in `INTEGRATION.md`.

## Honest limits

`agents/inception/HONEST-LIMITS.md`.
