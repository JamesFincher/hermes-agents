# HDR audit 05 — governor + budget

Base: `main` @ `4019e7cf061c34f6f3d6b74025f66c4f1663aa07`

**Slice:** Budget Governor, effort tiers, saturation, token economics, HARD overspend still writes a brief.

**Spec sections walked:** §3.3, §3.6, §8, plus governor hooks in §5.7 and budget fields on `research_plan` in §5.4. Adjacent sentences in §4.2 (the `config.yaml` numbers §8 depends on), §5.2/`gap_scan`, §5.6 (`hdr.effort` + volatile digest), P8 acceptance, and §13 (budget numbers are starting points) are cited when they bind a number or a behavior this slice owns.

**Mode:** discovery only. No production code was edited. This file is the only intended change.

**Hermes probe:** Context7 `/nousresearch/hermes-agent` first (2026-08-27). Official hook and `agent.run_budget_seconds` pages quoted below. `https://hermes-agent.nousresearch.com/llms.txt` timed out from this environment; HERMES-FACTS.md (same probe date, same library) and the Context7 snippets were used as the fallback.

**Classification key**

| Tag | Meaning |
| --- | --- |
| MATCH | Code implements the spec sentence (or the official STOP that correctly overrides the spec). |
| GAP | Spec requires it; code does not do it, or the test only pretends it does. |
| DRIFT | Something exists, but the number, trigger, or behavior is different from the spec with no note. |
| EXTRA | Code or config does something the spec did not ask for (or the spec asked for something official STOP forbids). |
| UNPROVEN | A claim is asserted (spec, test, or comment) without a live-Hermes or even an in-process hook proof. |

Severity: **blocker** (silent fail / circuit breaker does not trip / budget can be reset while HARD) · **major** (accounting wrong enough to miss AMBER/RED/HARD, or saturation is not computed as specified) · **minor** (allowlist wider than "brief path", unused fields) · **docs** (spec/code/honest-limits disagree in writing only).

---

## 0. Verdict

The Governor is real code, not a prompt. Thresholds 60 / 85 / 100 are implemented. Tier envelopes in `TIER_BUDGET` use the §3.6 starting-point numbers. AMBER named-gap fan-out is implemented in both `pre_tool_call` and `worker_brief`. RED blocks network tools. HARD blocks most tools and still *allows* a brief write.

That is not the same as "HARD overspend still writes a brief."

`store.draft.draft_brief` can produce a ledger-only brief, and `tests/test_hdr_plugin.py:test_governor_forced_overspend` calls it after a **hand-mutated** spend field. Nothing in the runtime calls `draft_brief` when the governor flips to HARD. The digest line `"synthesize now from the ledger"` is a prompt. The design rule in spec §0 is: *anything that can be computed deterministically must not be prompted.* The circuit breaker therefore stops fetching and then hopes the model writes a file.

Worse, the circuit breaker is only as good as the spend counters:

- Token spend is incremented in `hooks/governor.py` from `pre_api_request` / `post_api_request`. Those hooks are registered. They are **not tested**. The addition rule can double-count input tokens if `usage` carries `total_tokens`. Child-agent tokens are UNPROVEN.
- Fetch spend increments on `post_tool_call` for `NETWORK_TOOLS`, including searches. Terminal / skill fetches and `evidence_add` do not increment.
- Wall-clock spend (`spend.seconds`) is **never incremented**. `spend.started_at` is written and never read. `governor_state` therefore cannot reach HARD from elapsed time. Spec §3.3 HARD trigger `"≥ 100 % or run_budget_seconds elapsed"` is a stub on the clock side.

A 3-worker parent staying under 4 k tokens is proven only for `worker_brief` text plus `worker_harvest` JSON in a unit test, not for parent context growth across a real batch.

**Bottom line:** the Governor is a deterministic fence with the right state names and the right tier table. Spend accounting is partial. HARD-does-not-silent-fail is a test that writes the brief itself. Saturation is a yield ratio, not the compound stopping rule.

---

## 1. Files actually read

| Path | Why |
| --- | --- |
| `docs/HDR-SPEC.md` | Source of truth. §3.3, §3.6, §8, §5.4, §5.7, plus binding neighbors. |
| `docs/HERMES-FACTS.md` | Official hook / `run_budget_seconds` quotes. STOP on `moa`. |
| `docs/HONEST-LIMITS.md` | "Budget numbers are starting points." |
| `docs/research-bot-deep-dive.md` | Shipped summary of governor + config knobs. |
| `agents/research-bot/config.yaml` | `agent.run_budget_seconds`, compression, tool_output, delegation concurrency. |
| `agents/research-bot/plugins/hdr/hooks/governor.py` | `pre_api_request` / `post_api_request`. |
| `agents/research-bot/plugins/hdr/hooks/policy.py` | AMBER / HARD / fetch spend. |
| `agents/research-bot/plugins/hdr/hooks/prompt.py` | `hdr.effort`, AMBER/RED digest lines. |
| `agents/research-bot/plugins/hdr/hooks/lifecycle.py` | Session archive; no clock tick. |
| `agents/research-bot/plugins/hdr/hooks/subagents.py` | Child stamp; no child token fold-in. |
| `agents/research-bot/plugins/hdr/hooks/intake.py` | Intake does not increment fetch spend. |
| `agents/research-bot/plugins/hdr/store/run.py` | `TIER_BUDGET` application, `governor_state`, `add_spend`. |
| `agents/research-bot/plugins/hdr/store/draft.py` | Ledger-only brief. Not a tool. |
| `agents/research-bot/plugins/hdr/store/bus.py` | `append_audit`. |
| `agents/research-bot/plugins/hdr/tools/plan.py` | `research_plan`, `gap_scan`. |
| `agents/research-bot/plugins/hdr/tools/fanout.py` | AMBER named-gap fan-out. |
| `agents/research-bot/plugins/hdr/tools/evidence.py` | `evidence_add` does not add fetch spend. |
| `agents/research-bot/plugins/hdr/tools/retrieval.py` | Scholar/archive HTTP; fetch count only if `post_tool_call` sees the tool name. |
| `agents/research-bot/plugins/hdr/runtime.py` | `TIER_BUDGET`, `NETWORK_TOOLS`, `READ_ONLY_WHEN_HARD`. |
| `agents/research-bot/plugins/hdr/plugin.yaml` | Hook registration list. |
| `agents/research-bot/plugins/hdr/__init__.py` | `register()` wires governor hooks. |
| `agents/research-bot/plugins/hdr/schemas.py` | `research_plan` / `gap_scan` / `worker_brief` schemas. |
| `agents/research-bot/SOUL.md` | "If the budget runs out, deliver what is supported." |
| `agents/research-bot/skills/deep-research-run/SKILL.md` | Prompted loop; trusts saturation; no HARD auto-draft. |
| `tests/test_hdr_plugin.py` | HARD overspend, AMBER named-gap, 3-worker, fetch counter. |
| `evals/gates.py`, `evals/run_offline.py`, `evals/fixtures/run_a/audit.json` | Offline gates use fixture `wall_seconds`, not live spend. |

---

## 2. §3.3 — The Budget Governor, sentence by sentence

### 2.1 Spec quote

> `pre_api_request` and `post_api_request` are observer hooks carrying `approx_input_tokens` and `usage` `[DOC]`.

**MATCH (docs + registration).** HERMES-FACTS.md §3: `pre_api_request` payload includes `approx_input_tokens`; `post_api_request` includes `usage`; return ignored. Context7 `/nousresearch/hermes-agent` confirms observer hooks, `usage` on `post_api_request`, and that `pre_api_request` return values are not read. `plugin.yaml` lists both hooks. `hdr/__init__.py:register` calls `ctx.register_hook("pre_api_request", …)` and `ctx.register_hook("post_api_request", …)`.

`governor.pre_api_request` reads `approx_input_tokens` (named parameter) and, if that is 0, `kwargs["usage"]["prompt_tokens"]`. `governor.post_api_request` reads `usage` as a named parameter or `kwargs["usage"]`.

**UNPROVEN / major.** No unit test calls `pre_api_request` or `post_api_request`. Live payload shape is not locked. Official `CanonicalUsage` (Context7, `agent/usage_pricing.py`) uses `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`, with `prompt_tokens` and `total_tokens` as **properties**, not necessarily dict keys. If Hermes passes a dataclass or a dict of the dataclass fields, `isinstance(payload, dict)` is false for the object case (silent no-op in `post_api_request`) and `payload.get("total_tokens")` is missing for the field-dict case (falls through to `output_tokens`, which is fine). If some providers put `total_tokens` in the raw `usage` dict, see §2.2.

### 2.2 Spec quote

> The plugin accumulates per-run token and wall-clock spend in `run.json` and enforces it in `pre_tool_call`:

**PARTIAL — split below.**

Token accumulation: `run.add_spend(tokens=…)` from both API hooks. Persisted on `run.json` under `spend.tokens`. **MATCH (structure).**

Wall-clock accumulation: `empty_run` writes `spend.seconds: 0` and `spend.started_at`. `add_spend` can add `seconds`. **No caller passes `seconds`.** Grep of the plugin: `add_spend(` is only `governor.py` (tokens) and `policy.post_tool_call` (fetches). `lifecycle.py` does not tick the clock. `governor_state` uses `spend.seconds / budget.seconds`, not `now - started_at`.

**GAP, blocker.** Wall-clock spend is a stub. HARD cannot fire from elapsed time.

Enforcement: `policy.pre_tool_call` reads `current["governor"]` (the stored label) and calls `_delegate_fence` then `_budget_fence`. It does **not** recompute `governor_state(current)` at fence time. If the stored label is stale (seconds elapsed, or spend patched without `governor_state`), the fence uses the stale label.

**DRIFT, major.** Enforcement trusts a cached label. Spec says the plugin accumulates spend and enforces it — implying live ratios.

Fail-open: `pre_tool_call` wraps the whole body in `except Exception: return None`. A bug in the fence *allows* the tool. Official timeout path for `pre_tool_call` is fail-closed (HERMES-FACTS: "Timed-out or still-running `pre_tool_call` callbacks fail closed"). Plugin-level fail-open is the opposite of a circuit breaker.

**GAP, major.** Fence fails open on exception.

Audit of block decisions: spec §5.5 `audit/<run_id>.jsonl` is "every tool call, token delta, block decision." `policy.pre_tool_call` does not `append_audit` on a budget block. `post_tool_call` logs `{tool, duration_ms}` only. Token deltas are logged only when the API hooks succeed.

**GAP, minor** (audit completeness) overlapping **docs**.

### 2.3 GREEN — `< 60 % of tier budget` · normal

`run.governor_state`: `ratio = max(token_ratio, fetch_ratio, second_ratio)`; GREEN if `ratio < 0.60`.

**MATCH.** Using the max of three ratios is stricter than "tier budget" as tokens-only and is the right reading of "budget" given §5.4's three fields. Seconds never move, so the clock cannot pull GREEN into AMBER by itself.

### 2.4 AMBER — `≥ 60 %` · block new `delegate_task` batches; allow depth on named gaps only; one-line budget note in `pre_llm_call`

Threshold: `ratio >= 0.60` and `< 0.85`. **MATCH.**

`delegate_task` fence: `policy._delegate_fence`. GREEN → allow. RED/HARD → block all. AMBER → allow only if `_matches_named_gap(goal, _named_gaps(current))`. **MATCH** for the later close ("named-gap fan-out under AMBER is allowed").

Named-gap source: `named_gaps` if set, else `open_questions`. `gap_scan` writes `named_gaps = unanswered`. **MATCH** once `gap_scan` has run. Before the first `gap_scan`, AMBER falls back to all `open_questions`, so every planned question still matches. That is looser than "named gaps only."

**DRIFT, minor.** AMBER before `gap_scan` treats every open question as a named gap.

Matching algorithm in policy (`_matches_named_gap`): lowercase containment, or `blob[:80] in needle`, or first 40 chars of a ≥12-char needle. Matching in `fanout.worker_brief`: `question == item` or `question[:40] in item` or `item[:40] in question`. Two different predicates.

**DRIFT, minor.** A `delegate_task` goal can pass the hook and still be refused by `worker_brief`, or the reverse.

`worker_brief` under AMBER: refuses unless the `open_question` matches `named_gaps` / `open_questions`. Tested by `test_amber_named_gap_depth`. **MATCH.**

One-line budget note: `prompt.digest_text` appends `"AMBER: no new worker batches. Depth on named gaps only."` when `governor == "AMBER"`. Cap 1 200 chars. **MATCH.**

The digest also always prints `governor: {state}` and `budget {pct}%`. EXTRA relative to "one-line," harmless.

### 2.5 RED — `≥ 85 %` · block all network tools; `pre_llm_call` injects "synthesize now from the ledger"

Threshold: `ratio >= 0.85` and `< 1.0`. **MATCH.**

`_budget_fence`: if RED and `tool_name in NETWORK_TOOLS`, block with `"Governor RED: block network tools. Synthesize now from the ledger."` **MATCH** for the listed network set.

`NETWORK_TOOLS` (`runtime.py`): `web_search`, `web_extract`, `browser_navigate`, `browser_snapshot`, `x_search`, `docs_query`, `resolve_library`, `scholar_search`, `archive_lookup`.

Not in the set: `terminal`, `execute_code`, `evidence_add`, `browser_vision` / `vision_analyze`. A RED run can still curl via `terminal` or pull figures via vision.

**GAP, major.** RED does not block all retrieval, only the named network tools. Spec: "block all network tools." Terminal egress is a network tool in any research-agent reading of that sentence.

`_delegate_fence` blocks all `delegate_task` on RED. `worker_brief` refuses RED/HARD. **MATCH.**

Digest: `if governor in {"RED", "HARD"}: lines.append("synthesize now from the ledger. No new fetches.")` **MATCH** (wording is the spec string plus a second sentence).

**UNPROVEN.** No test sets RED and asserts a network block. The HARD test jumps tokens to 100%+ and never parks in the 85–99 band.

### 2.6 HARD — `≥ 100 % or run_budget_seconds elapsed` · block everything except `read_file`, ledger tools, and `write_file` under the brief path

Token/fetch/seconds ratio `>= 1.0` → HARD. **MATCH** for the percentage trigger.

`run_budget_seconds elapsed`:

- Spec §3.3 names Hermes' `agent.run_budget_seconds` in the next sentence as the clock twin, and HARD's own trigger as "`run_budget_seconds` elapsed."
- Official (Context7, configuration.md): `agent.run_budget_seconds` is optional; wrap-up notice at 80%; **the budget resets on each user message**; implicit stale timeouts are capped. It is a per-user-message wall clock, not a per-research-run clock.
- Shipped `config.yaml` sets `agent.run_budget_seconds: 1800` (30 minutes) for every tier. Tier envelopes are 90 s / 360 s / 1200 s / 3600 s.
- Plugin HARD does not read Hermes' remaining budget. It only looks at `spend.seconds / budget.seconds`. `spend.seconds` is never incremented.

**GAP, blocker** (plugin clock never trips). **DRIFT, major** (Hermes 1800 s reset-per-message is not the tier clock, and exhaustive's 3600 s envelope is longer than the Hermes wrap-up). **docs** (spec §3.3 pairs two different clocks without saying so).

Allowed tools when HARD: `READ_ONLY_WHEN_HARD` =

```
read_file, evidence_read, evidence_search, evidence_stats, gap_scan,
claim_verify, conflict_report, cite_source, research_plan,
worker_harvest, write_file, patch
```

Spec allow list: `read_file`, ledger tools, `write_file` under the brief path.

| Tool | Spec HARD | Code HARD |
| --- | --- | --- |
| `read_file` | allow | allow |
| `evidence_*` / `gap_scan` / `claim_verify` / `conflict_report` / `cite_source` | ledger tools → allow | allow |
| `write_file` / `patch` | brief path only | allowed in fence; path still goes through `_write_allowlist` (`notes/ research/ briefs/ findings/ citations/ sources/ data/`) |
| `worker_harvest` | not named | allow (EXTRA, reasonable) |
| `research_plan` | not named | allow — **can rewrite `budget` if `tier` is sent** |
| `evidence_add` | not named | **block** |
| `todo` / `memory` / `session_search` | "block everything except …" | early `return None` (allow) because they are intercepted |
| `terminal` / `execute_code` / `delegate_task` / network tools | block | block (network via fence; delegate via `_delegate_fence`) |

**DRIFT, major:** `research_plan` remains callable on HARD and `plan.research_plan` will replace `budget` from `TIER_BUDGET` whenever `args.tier` is a known tier. That is a HARD escape hatch.

**DRIFT, minor:** write allowlist is seven directories, not "the brief path." Citation Gate still applies, so a HARD write of a sloppy brief can still be refused — which fights "still writes a brief."

**EXTRA, minor:** `worker_harvest` on HARD.

**GAP, minor vs §3.3 wording / MATCH vs §5.7 intercepted-tool rule:** `todo`/`memory`/`session_search` are not blocked on HARD because §5.7 says return `None` for intercepted tools. Two spec sentences disagree; code follows §5.7.

### 2.7 Spec quote

> Pair with Hermes' own `agent.run_budget_seconds`, which injects a one-time wrap-up notice at 80 % of the wall-clock budget `[DOC]`. The Governor is the token-side twin of that clock.

**MATCH (config knob).** `config.yaml` `agent.run_budget_seconds: 1800`. HERMES-FACTS and Context7 confirm the 80% one-time wrap-up.

**DRIFT, major (semantics).** Official clock resets per user message. HDR run.json is per research run. They are not twins. A multi-turn research job gets a fresh Hermes wrap-up on every user ping, and never a plugin HARD from wall time.

**DRIFT, docs.** One profile-level 1800 s cannot be the twin of four tier clocks (90 / 360 / 1200 / 3600). For `quick` and `standard`, Hermes will not wrap up before the tier envelope expires (if the plugin clock worked). For `exhaustive`, Hermes wraps up at 1440 s while the tier envelope is 3600 s.

Do not invent a per-tier Hermes knob. The fix is to tick `spend.seconds` from `started_at` (or from `duration_ms`) against `TIER_BUDGET[tier].seconds`, and to document that `agent.run_budget_seconds: 1800` is a coarse host backstop, not the tier clock.

---

## 3. §3.6 — Effort scaling and saturation, sentence by sentence

### 3.1 Spec quote

> Explicit tiers, stated in a cache-safe system-prompt section so they cost tokens once per session, not once per turn:

**MATCH.** `prompt.register_sections` registers `hdr.effort` via `ctx.register_system_prompt_section(..., position="after_memory")`. Test `test_register_surfaces` asserts the three section names and the 4 k / 8 k caps.

`hdr.effort` is 430 characters (spec guessed ~900). Still well under 4 000. **DRIFT, docs** (size guess only).

### 3.2 Tier table

| Tier | Spec trigger | Spec workers | Spec fetches | Spec tokens | Spec wall | `TIER_BUDGET` (`runtime.py`) | `hdr.effort` text |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `quick` | single fact, one entity | 0 (inline) | ≤ 5 | 40 k | 90 s | tokens 40000, fetches 5, seconds 90, workers 0 | "0 workers, ≤5 fetches, 40k tokens, 90s" |
| `standard` | comparison, state of X | 2–3 | ≤ 25 | 200 k | 6 min | 200000 / 25 / 360 / workers 3 | "2–3 workers, ≤25 fetches, 200k tokens, 6 min" |
| `deep` | survey, diligence | 4–6 | ≤ 80 | 800 k | 20 min | 800000 / 80 / 1200 / workers 6 | "4–6 workers, ≤80 fetches, 800k tokens, 20 min" |
| `exhaustive` | explicit user request only | 6–10, depth 2 | ≤ 250 | 3 M | 60 min | 3000000 / 250 / 3600 / workers 10 | "6–10 workers, depth 2, ≤250 fetches" (tokens/seconds omitted in the prompt line) |

**MATCH.** The code uses the spec starting-point numbers, not a silent other table. 6 min = 360 s, 20 min = 1200 s, 60 min = 3600 s. `workers` is the top of each range. `hdr.effort` omits exhaustive's 3 M / 60 min in the prompt line — **DRIFT, docs**, not a budget bug.

`research_plan` copies `dict(TIER_BUDGET[tier])` into `run.json.budget`. Return shape includes `budget.tokens`, `budget.fetches`, `budget.seconds`, and also `budget.workers` (EXTRA vs the §5.4 sketch `{"tokens","fetches","seconds"}`, harmless).

**GAP, major:** `TIER_BUDGET[*].workers` is stored and never enforced. Nothing blocks a fourth `delegate_task` on `standard`, or any worker on `quick` (spec: 0, inline). `delegation.max_concurrent_children: 5` is a Hermes concurrency cap, not a per-tier worker cap. `quick` can still fan out. The skill says "Do not start fifty workers for a one-fact question" — a prompt, which violates the design rule.

`max_spawn_depth: 2` MATCHES exhaustive "depth 2" as a profile-wide Hermes knob, not a per-tier switch. `standard` can also spawn depth 2.

Default tier: plugin setting `default_tier: standard` MATCHES §5.4 / §4.2.

### 3.3 Saturation rule

> stop breadth when the last worker batch produced **< 20 % new tier-A/B sources** and every open question in `run.json` has ≥ 2 independent supporting sources, or when the Governor hits AMBER. `gap_scan` computes and returns this number; the model does not estimate it.

Three claims:

1. The number is computed, not guessed.
2. The number encodes (last-batch A/B yield < 0.20) AND (every open question has ≥ 2 independent supports), OR governor is AMBER.
3. The model is told to trust the number (`hdr.effort`, skill, digest).

What `plan.gap_scan` actually does:

```
new_count = count of last_batch_ids whose source.tier is A or B
yield_ratio = new_count / len(last_batch_ids)   # 0.0 if last_batch_ids empty
saturation = yield_ratio
```

`last_batch_ids` is written by `fanout.worker_harvest` as **all ledger ids not in the previous `last_batch_ids`**, plus any URLs scraped from a transcript. It is "new since last harvest," not "new tier-A/B sources produced by the last worker batch" as a fraction of that batch's sources. The unused local `prior = max(1, len(sources) - len(last_ids))` looks like a discarded denominator.

Support test for an open question:

```
support = sources where question[:24] in title or quote, OR src.tier in {A,B}
independent = set of canonical_url/url of support
if len(independent) < 2: unanswered
```

`OR src.tier in {A,B}` means **any two A/B sources in the run count as support for every open question**, regardless of topic. One harvest of two unrelated A/B pages marks every question answered.

`recommend`:

- `"depth"` if `unanswered` and governor in `{None, "GREEN"}`
- `"synthesize"` default, or if AMBER/RED
- `"stop"` if HARD

AMBER therefore recommends `"synthesize"` (stop breadth), which MATCHES "or when the Governor hits AMBER" as a *recommendation*, not as a saturation number. The returned `saturation` field is still just `yield_ratio`. It does not become 1.0 on AMBER. It does not AND with the ≥2-supports predicate. Spec example values (`saturation: 0.14`, `new_source_yield: 0.18`) imply they were imagined as **different** numbers; the code sets both to `yield_ratio`.

**GAP, major.** Saturation is not the compound stopping rule. It is last-batch A/B yield, with a broken "independent support" side computation that is only used for `unanswered` / `recommend`, and that side computation is itself wrong.

**MATCH (intent, weak):** a float is returned; the model is told not to estimate it. `test_plan_digest_and_gap_scan` only asserts `isinstance(scan["saturation"], float)`. P5 acceptance ("returns a real saturation number") is met as "a float exists."

**DRIFT, major:** the 20 % threshold never appears in code. Nothing compares `yield_ratio` to 0.20 except the prompt text in `hdr.effort`. Stopping is `recommend` plus the model's willingness to obey it — again a prompt, except when the Governor is already AMBER/RED/HARD.

---

## 4. §8 — Token economics, row by row

§8 is a table of mechanisms. Each row is a savings claim plus a knob. Spec: "Report these per run in the audit file so the numbers are measured, not asserted."

| Mechanism | Spec knob | Shipped? | Audit measured? | Class |
| --- | --- | --- | --- | --- |
| Evidence Cards replace page text | `transform_tool_result` | Yes. `test_evidence_bus_card_and_byte_exact` asserts card ≤400 tokens on a >40 k-char page. | Not in run audit as a per-page ratio. | MATCH (mechanism). UNPROVEN (per-run measurement). |
| Dedupe fence | `pre_tool_call` | Yes. `web_extract` / `browser_navigate` + 15-minute query hash. | Block decisions not written to audit. | MATCH (mechanism). GAP (audit row). |
| Cheap workers | `delegation.model` | **Not set in git.** Comment: set on the host; empty inherits parent (official). | — | MATCH official / host-set. **UNPROVEN** that workers are cheap. If unset, children inherit the frontier model and §8's biggest saving is off. |
| Proactive prune | `compression.proactive_prune_tokens: 48000` | `config.yaml` 48000. Also `proactive_prune_min_result_chars: 4000`, `proactive_prune_min_reclaim_tokens: 8192`. | Hermes-side, not HDR audit. | MATCH number. |
| Lean tail | `compression.tail_mode: lean` | `lean`. | Hermes-side. | MATCH. |
| 1-hour prompt cache | `prompt_caching.cache_ttl` | `"1h"`. Official honors only `5m` / `1h`. HERMES-FACTS: "across forked children" is `[INF]`. | — | MATCH knob. UNPROVEN for children. |
| Static contract in a prompt section | `register_system_prompt_section` | `hdr.method` / `hdr.effort` / `hdr.integrity`. | — | MATCH. |
| Volatile digest cap 1 200 chars | `pre_llm_call` | `digest_text` truncates at 1200. Test asserts `len(context) ≤ 1200`. | — | MATCH. |
| Cheap compression model | `auxiliary.compression` | `reasoning_effort: "low"`, `max_concurrency: 2`. **No `model` / `fallback_chain`.** Spec §4.2 pins a cheap model. | — | DRIFT / GAP vs §4.2 (model pin). MATCH vs "do not invent model ids" / host-set policy in the shipped config header. |
| MCP spillover | `tool_budget.mcp_result_size_chars` | 30000. | Hermes-side. | MATCH. |
| Scripts instead of inline parsers | `${HERMES_SKILL_DIR}` | Skills exist. | — | MATCH (out of slice except as a claimed saving). |
| Transcript grep instead of transcript reading | `execute_code` over live logs | `worker_harvest` reads the log in **plugin Python**, not via `execute_code`. Returns counts. | — | DRIFT (cheaper, actually). MATCH (parent does not load raw pages). |
| Deterministic bibliography | `transform_llm_output` | Yes. Zero inference. | — | MATCH. |

`tool_output.max_bytes: 40000`, `max_lines: 1500`, `max_line_length: 1200` MATCH §4.2.

`compression.threshold: 0.55`, `threshold_tokens: 220000`, `protect_last_n: 12`, `protect_first_n: 2`, `in_place: true`, `idle_compact_after_seconds: 1800`, `context_timeout_seconds: 180` MATCH §4.2.

`delegation.max_concurrent_children: 5`, `max_iterations: 30`, `max_spawn_depth: 2`, `child_timeout_seconds: 900` MATCH §4.2 (deep wants 5 concurrent). This is **not** the §3.6 per-tier worker count.

`file_read_max_chars: 150000`, `context_file_max_chars: 20000`, `prompt_caching.cache_ttl: "1h"`, `agent.max_turns: none`, `agent.api_max_retries: 2`, `session_stall_timeout: 300`, `verify_on_stop: false` MATCH §4.2.

§8 last sentence: report the savings per run in the audit file. `append_audit` writes hook events and tool names. It does not write tokens-per-A/B-source, card-vs-page ratios, or prune reclaim. Eval fixtures carry a hand-written `audit.json` with `tokens` / `tier_ab_sources` / `wall_seconds` that `evals/gates.py` checks — **not** produced by the plugin.

**GAP, docs/major.** The economics table is configured; it is not measured per run.

---

## 5. §5.4 — `research_plan` budget fields

Spec schema:

```
{"action": {create, update, status},
 "question", "tier": {quick, standard, deep, exhaustive} default standard,
 "open_questions", "falsifiers",
 "constraints": {since, domains, exclude}}
→ {"run_id","tier","budget":{"tokens","fetches","seconds"},"open_questions","phase"}
```

`plan.research_plan`:

- `action` default `"create"`. `status` dumps the current run. `update` loads or `empty_run()`. else `empty_run(question, tier)`.
- Applies question, tier (and **resets budget** from `TIER_BUDGET`), open_questions, falsifiers, constraints.
- Recomputes `governor` via `governor_state`.
- Returns `ok, run_id, tier, budget, open_questions, phase, governor`.

**MATCH** on the documented return keys. EXTRA: `ok`, `governor`, `budget.workers`.

`tier` is not enum-validated in the JSON schema (`schemas.RESEARCH_PLAN` is a free string). Unknown tiers fall through `empty_run` to `default_tier` / `standard`. **MATCH** behavior, **DRIFT** vs the spec enum (schema is loose).

`test_plan_digest_and_gap_scan` asserts `plan["budget"]["tokens"] == 200000` for `standard`. **MATCH** starting-point number.

Updating `tier` on an in-flight run resets the envelope and does not scale spend. Combined with HARD allowing `research_plan`, this is the escape hatch in §2.6.

`constraints` are stored and not applied to the Governor or to fetch spend. Out of slice except as a dead field on the same object.

---

## 6. §5.7 — Governor hooks

| Hook | Spec use | Code | Class |
| --- | --- | --- | --- |
| `pre_tool_call` | Budget fence per §3.3 | `policy.pre_tool_call` → `_delegate_fence` + `_budget_fence` | MATCH (wired). See §2 for holes. |
| `post_tool_call` | audit log, per-tool latency, **fetch counter** | logs `{tool, duration_ms}`; `if tool_name in NETWORK_TOOLS: add_spend(fetches=1)` | MATCH (counter exists). See §8 of this audit for "real retrieval." |
| `pre_api_request` / `post_api_request` | Budget Governor accounting | `governor.py` | MATCH (wired). UNPROVEN (payload). See §2.1–2.2. |
| `pre_llm_call` | ≤1200-char digest; AMBER note; RED "synthesize now" | `prompt.pre_llm_call` | MATCH. |
| `subagent_start` / `subagent_stop` | stamp children; count child tool calls | stamps status; stores `kwargs.tool_calls` if present; **does not add child tokens or fetches** | MATCH (stamp). GAP (child spend). |

§5.7 detail 1: return `None` for intercepted `todo`/`memory`/`session_search`; block `delegate_task` for AMBER/RED fan-out. **MATCH.** Official now `[DOC]` that `pre_tool_call` can block `delegate_task` (HERMES-FACTS). The old `[UNV]` probe is resolved; code uses the hook, not the `worker_brief` fallback as the only fence. Both fences exist (defense in depth). **MATCH.**

§5.7 detail 3: "Budget fence per §3.3." Covered in §2.

Fail-open on `pre_api_request` / `post_api_request`: both `except Exception: return`. A hook error drops the increment and leaves the governor GREEN. **GAP, major** for a circuit breaker (opposite of fail-closed). Acceptable for observer hooks per official "return ignored" / fail-open on non-`pre_tool_call` timeouts. The combination is: accounting fails open, fence fails open, only Hermes' own 80% wrap-up (reset per message) remains.

---

## 7. HARD overspend still writes a brief?

### 7.1 What the spec and the task require

P8 acceptance (spec §11):

> A forced-overspend fixture stops fetching and produces a brief from what it has

Task text:

> HARD must still write a ledger-only draft brief — never silent fail.

SOUL Defaults:

> If the budget runs out, deliver what is supported and list what is still open.

Design rule (spec §0):

> anything that can be computed deterministically must not be prompted.

### 7.2 What the test does

`tests/test_hdr_plugin.py:test_governor_forced_overspend`:

1. `research_plan({question: "overspend", tier: "quick"})`.
2. **Mutates** `current["spend"]["tokens"] = budget.tokens + 10`.
3. Sets `current["governor"] = governor_state(current)` and saves.
4. Asserts `governor == "HARD"`.
5. `pre_tool_call("web_extract", …)` → `action == "block"`.
6. `ledger.add_source(...)` directly (not through a tool).
7. `evidence_search` works.
8. `draft = store.draft.draft_brief()` — **test calls the library function**.
9. Asserts `draft["brief"]` is nonempty and contains `[S1]`.
10. `pre_tool_call("write_file", {path: "briefs/partial.md", content: draft["brief"]})` is `None` (allowed).

This proves:

- `governor_state` can return HARD if tokens are already over the cap.
- `web_extract` is blocked when the stored label is HARD.
- `draft_brief` can render a brief from the ledger.
- `write_file` of that brief under `briefs/` is not blocked by the fence or the Citation Gate.

This does **not** prove:

- A live run that crosses 100% via `pre_api_request` / `post_api_request` becomes HARD.
- HARD from fetches or seconds.
- The plugin writes a brief without the model (or the test) calling `draft_brief`.
- Chat delivery without `write_file` (Citation Gate does not run on chat; `transform_llm_output` only flags uncited stats).
- That `draft_brief` is reachable as a tool. It is **not registered**. `schemas.ALL` has no `draft_brief`. The model cannot call it.

### 7.3 What the runtime does on HARD

1. Digest tells the model to synthesize.
2. Skill `deep-research-run` says write under `briefs/` or `research/`.
3. SOUL says deliver what is supported.
4. No hook on the GREEN→HARD edge calls `draft_brief` or `write_file`.
5. If the model stops, or if Citation Gate refuses a model-authored brief, the user gets no file.

**GAP, blocker** vs "never silent fail" and vs the design rule. The test's name claims P8; the test authors the brief.

`draft_brief` itself is ledger-only, no network, no prompt. That part MATCHES "ledger-only draft brief" as a function. Wiring is the gap.

`draft_brief` unanswered logic is crude: it treats *every* open question as unanswered when `len(A/B sources) < 2` globally, not per question. Still produces text. Empty ledger produces "I did not find a reliable source for: {question}." plus a "Not found" list. That is a valid brief.

---

## 8. Does a 3-worker parent stay under the spec token bound if tests claim that?

P6 acceptance (spec §11):

> 3 parallel workers on disjoint mandates; parent context grows < 4 k tokens across the whole batch; zero raw page text in the parent

`test_three_worker_batch_parent_stays_small`:

- Creates a `standard` plan with three mandates.
- For each: `worker_brief` then writes a live log containing `FINDING:` + a URL, then `worker_harvest`.
- Concatenates the three briefs and three harvest JSON dumps.
- Asserts `tokens = (len(parent_text)+3)//4 < 4000`.
- Asserts harvest JSON has no `"RAW"` and no secret page body.

What it does **not** do:

- Call `delegate_task`.
- Measure conversation history, tool-result cards, or `pre_llm_call` digest accumulation.
- Run three workers concurrently (`max_concurrent_children`).
- Include Evidence Cards the parent would see if it fetched (parent is not supposed to).
- Count tokens the way Hermes counts them.

A single `worker_brief` body is on the order of 200–250 tokens. Three briefs plus three small harvest objects fit under 4 k easily. That is a test of string length, not of parent context growth.

**UNPROVEN** for the spec sentence. **MATCH** for "harvest returns no raw page text" (narrower, true).

If a reviewer treats the test name as a 4 k parent-context guarantee, that claim is not earned.

---

## 9. Spend accounting — real or stub?

### 9.1 Tokens

Path: `governor.pre_api_request` → `add_spend(tokens=approx_input_tokens or usage.prompt_tokens)` then `governor.post_api_request` → `add_spend(tokens=usage.total_tokens or usage.output_tokens or usage.completion_tokens)`.

Intended reading (if pre = input, post = output): sum is the call. **UNPROVEN.**

Failure modes:

1. `usage.total_tokens` present (many OpenAI-shaped dicts): post adds input+output after pre already added input. **Double-count. DRIFT, major** if that payload exists.
2. `usage` is `CanonicalUsage` dataclass: `isinstance(..., dict)` is false; post adds 0. Pre may still add `approx_input_tokens`. **Under-count. GAP, major.**
3. Both hooks fire with overlapping keys. No idempotency, no `api_request_id` dedupe. Official payloads include `api_request_id` (Context7 observability README). Code ignores it.
4. Child API calls: if the child process loads the hdr plugin against the same `plugin-data/hdr/run.json`, child tokens land in the same spend (good). If children do not run parent hooks, child tokens — "where the tokens go" per spec §4.2 — are invisible and the Governor never sees the majority of spend. **UNPROVEN, major.**
5. `approx_input_tokens` is approximate. Using it *and* provider usage without reconciliation is messy.
6. No test.

`add_spend` does update `governor` after every increment. **MATCH** for the write path when a hook actually runs.

### 9.2 Fetches

`policy.post_tool_call`: `if tool_name in NETWORK_TOOLS: add_spend(fetches=1)`.

`test_fetch_counter_and_index_search` calls `post_tool_call("web_search", …)` and asserts `spend.fetches >= 1`. That is a **search**, not a page body.

Task text: "Fetch spend must increment on real retrieval, not only on model tokens."

| Retrieval path | Increments fetches? |
| --- | --- |
| `web_extract` / `browser_navigate` / `browser_snapshot` | Yes (`NETWORK_TOOLS`) |
| `web_search` / `x_search` | Yes — search counted as a fetch |
| `docs_query` / `resolve_library` / `scholar_search` / `archive_lookup` | Yes |
| `transform_tool_result` intake (actual corpus write) | **No** |
| `evidence_add` (PDF, terminal-fetched page, skill fallback) | **No** |
| `web-fallback-fetch` skill / `terminal` curl | **No** |
| Child `web_extract` | Only if child's `post_tool_call` runs in a process that shares `run.json` |

**DRIFT, major.** Fetch spend is "network-shaped tool returned," not "a page entered the corpus." Searches burn the fetch budget; the skill fallback that the spec says must complete the run does not.

Blocked tools still hit `post_tool_call` officially ("After blocked, error, or successful result"). A blocked second `web_extract` can increment fetches. **DRIFT, minor.**

### 9.3 Seconds

`spend.seconds` is only changed by `add_spend(seconds=…)`. No caller. `started_at` is dead. `post_tool_call` receives `duration_ms` and does not convert it.

**GAP, blocker.** Wall-clock budget is decorative.

### 9.4 `pre_tool_call` does not refresh ratios

Fence uses `current["governor"]`. Clock cannot flip the label between tool calls. Even a future seconds tick would need either `add_spend` or a `governor_state` recompute at the fence.

---

## 10. Config.yaml vs spec numbers (this slice)

| Knob | Spec §4.2 / §8 | `config.yaml` | Class |
| --- | --- | --- | --- |
| `delegation.max_concurrent_children` | 5 | 5 | MATCH |
| `delegation.max_iterations` | 30 | 30 | MATCH |
| `delegation.max_spawn_depth` | 2 | 2 | MATCH |
| `delegation.child_timeout_seconds` | 900 | 900 | MATCH |
| `delegation.model` | cheap worker | commented; host-set | MATCH (documented omission) |
| `auxiliary.compression.reasoning_effort` | low | low | MATCH |
| `auxiliary.compression.model` | cheap model | absent | DRIFT vs spec; MATCH host-set policy |
| `compression.proactive_prune_tokens` | 48000 | 48000 | MATCH |
| `compression.tail_mode` | lean | lean | MATCH |
| `compression.threshold` / `threshold_tokens` | 0.55 / 220000 | same | MATCH |
| `tool_output.*` | 40000 / 1500 / 1200 | same | MATCH |
| `tool_budget.mcp_result_size_chars` | 30000 | 30000 | MATCH |
| `agent.run_budget_seconds` | 1800 | 1800 | MATCH number. DRIFT vs per-tier clocks (see §2.7). |
| `custom_toolsets.research` includes `moa` | yes in §4.2 | **omitted** | MATCH official STOP. EXTRA in the spec. |
| `plugins.entries.hdr.mcp_allowlist` | context7, openalex, pubmed, wayback | `context7` only | MATCH official STOP / HERMES-FACTS (those servers are not first-party). HTTP facades remain. |

Budget numbers in §3.6 are starting points (spec §13, HONEST-LIMITS). Code uses those numbers as the starting points the spec wrote. **MATCH.** There is no silent other table.

---

## 11. Prompt vs deterministic code

The Governor's fences are code. The following stopping behaviors are still prompts:

- `hdr.effort` saturation paragraph (the 20 % rule).
- Digest `"synthesize now from the ledger"`.
- SOUL "If the budget runs out, deliver…"
- Skill "If it recommends synthesize or stop, stop fetching."
- Skill "Do not start fifty workers for a one-fact question."

No line says "please stop" as a raw string. The digest is the polite version of that. **DRIFT** vs "Do not prompt the model to please stop."

`TIER_BUDGET.workers` is not a fence. Worker count is prompted.

---

## 12. Tests that claim HARD overspend still writes a brief

Only one test is about HARD: `test_governor_forced_overspend`.

Related tests:

| Test | What it actually proves | What it does not prove |
| --- | --- | --- |
| `test_governor_forced_overspend` | Mutated token HARD blocks `web_extract`; `draft_brief()` text can be written to `briefs/` | Live accounting; auto-write; fetch/seconds HARD; RED band |
| `test_amber_named_gap_depth` | AMBER refuses a new-batch `worker_brief` and `delegate_task`; allows named-gap both | Matching-algorithm identity; AMBER before `gap_scan`; RED |
| `test_three_worker_batch_parent_stays_small` | Brief+harvest strings < 4000 tokens; no raw HTML in harvest | Parent context growth; concurrency; P6 |
| `test_fetch_counter_and_index_search` | `post_tool_call(web_search)` increments `spend.fetches` | Real retrieval; terminal/skill; blocked-call increment |
| `test_plan_digest_and_gap_scan` | standard tokens == 200000; digest ≤1200; saturation is a float | 20 % rule; per-question support; AMBER recommend |
| `test_web_fallback_completes_without_web_extract` | `evidence_add` + `draft_brief` works | Fetch counter on fallback |
| `evals/gates.py` wall / tokens-per-A/B | Fixture `audit.json` numbers | Plugin `spend` |

There is no test that:

- calls `pre_api_request` / `post_api_request`
- increments seconds
- reaches HARD via fetches
- asserts RED
- asserts `quick` cannot `delegate_task`
- asserts saturation `< 0.20` and ≥2 supports
- asserts HARD auto-emits a brief

---

## 13. Findings register (this slice)

| ID | Class | Sev | Finding |
| --- | --- | --- | --- |
| F01 | GAP | blocker | HARD does not write a brief. `draft_brief` is a library function used by the test and by `evals/run_offline.py`. No HARD-edge hook. Silent fail is possible. |
| F02 | GAP | blocker | `spend.seconds` is never incremented. `started_at` is unused. HARD cannot trip on time. |
| F03 | DRIFT | major | `agent.run_budget_seconds: 1800` is official per-user-message wrap-up, not the tier clock. Exhaustive 3600 s > 1800 s. |
| F04 | GAP | major | Token hooks untested; `total_tokens` can double-count; dataclass `usage` can no-op. |
| F05 | UNPROVEN | major | Child token/fetch spend may not enter parent `run.json`. |
| F06 | DRIFT | major | Fetch increment is "network tool returned," including searches; not corpus write; misses `evidence_add` / terminal / skill. |
| F07 | GAP | major | Saturation = last-batch A/B yield. 20 % threshold not in code. Per-question support ORs in any A/B source. |
| F08 | GAP | major | `TIER_BUDGET.workers` not enforced. `quick` can fan out. |
| F09 | DRIFT | major | HARD allows `research_plan`, which can reset `budget`. |
| F10 | GAP | major | RED does not block `terminal` / `execute_code` / `evidence_add`. |
| F11 | GAP | major | `pre_tool_call` fail-open on exception; fence uses cached `governor` label. |
| F12 | UNPROVEN | major | 3-worker < 4 k parent tokens is a string-length test. |
| F13 | GAP | docs/major | §8 "report these per run in the audit file" is not implemented. |
| F14 | DRIFT | minor | AMBER named-gap matchers differ between `policy.py` and `fanout.py`. |
| F15 | DRIFT | minor | HARD write path is the seven-dir allowlist, not "brief path." |
| F16 | EXTRA | minor | `budget.workers` returned; `worker_harvest` allowed on HARD. |
| F17 | MATCH | — | GREEN/AMBER/RED/HARD thresholds 60/85/100. |
| F18 | MATCH | — | Tier token/fetch/second starting points match §3.6. |
| F19 | MATCH | — | AMBER named-gap `delegate_task` + `worker_brief`. |
| F20 | MATCH | — | Digest AMBER line and RED/HARD "synthesize now from the ledger." |
| F21 | MATCH | — | §4.2 / §8 compression, tool_output, tool_budget, prune 48000, lean tail, cache 1h, digest 1200, hooks registered. |
| F22 | MATCH | — | No `moa` toolset; no invented academic MCP. Path install. Governor is code, not a new Hermes knob. |
| F23 | MATCH | — | Forced-overspend **test** stops `web_extract` and can write a ledger brief — as a test, not as a runtime guarantee. |

---

## 14. Numbered fix list (do not apply)

These are recommendations for a later closer. This audit does not implement them.

1. **HARD auto-brief (F01).** When `governor_state` first becomes HARD (inside `add_spend` or a `pre_tool_call` recompute), call `draft.draft_brief()` and write `briefs/<run_id>-partial.md` (or return it from the block message). Deterministic. No prompt. Keep `write_file` allowed so a model can replace it. Add a test that does **not** call `draft_brief` itself.

2. **Tick the clock (F02).** In `governor_state` or at the start of `pre_tool_call`, set `spend.seconds = now - parse(started_at)` (wall, not sum of tool durations). Do not invent a Hermes knob.

3. **Document the two clocks (F03).** In HONEST-LIMITS / deep-dive: `agent.run_budget_seconds: 1800` is a host backstop that resets per user message and wraps up at 80%. Tier HARD uses `TIER_BUDGET.seconds`. Note exhaustive 3600 vs 1800. Leave the YAML number as the spec's 1800 unless a later measurement says otherwise.

4. **Normalize usage (F04).** Prefer official `usage` fields: `input_tokens` + `output_tokens` (or `CanonicalUsage` attributes). Never add `total_tokens` after adding input. Dedupe on `api_request_id`. Unit-test `pre_api_request` / `post_api_request` with a dict, a `total_tokens`-only dict, and a namespace object.

5. **Prove or fold child spend (F05).** Probe whether child processes run hdr hooks against the same `run.json`. If not, have `subagent_stop` add `kwargs` usage / tool_calls into `spend`, or treat missing child spend as an honest limit.

6. **Fetch = corpus admission (F06).** Increment fetches when `transform_tool_result` or `evidence_add` writes a new corpus file (or a new ledger row with bytes). Do not increment on `web_search` alone. Do not increment on a dedupe block. Add a test for skill-fallback `evidence_add`.

7. **Compute saturation (F07).** `new_source_yield` = new A/B in last batch / sources in last batch. Per-question support = independent canonical URLs whose cards actually attach to that question (not "any A/B"). `saturation` = a single computed flag or a struct the spec already sketched (`saturation`, `new_source_yield`, `unanswered`). Compare yield to 0.20 in code. `recommend` stays deterministic. Delete the unused `prior` local or use it on purpose.

8. **Enforce workers (F08).** Fence `delegate_task` when `len(children running|briefed) >= budget.workers` (0 on `quick`). Do not prompt it.

9. **Lock `research_plan` on HARD (F09).** Remove it from `READ_ONLY_WHEN_HARD`, or ignore `tier`/`budget` writes when governor is RED/HARD. Status-only is enough.

10. **RED/HARD retrieval (F10).** Add `terminal` and `execute_code` to the RED network block when the command looks like egress (or block both on RED/HARD except allowlisted ledger reads). Keep `evidence_add` blocked on HARD (already) but allowed on RED so a just-finished child can register.

11. **Fence fail-closed (F11).** On exception in the budget/delegate fences, block with a short message (or recompute `governor_state` and only fail open when GREEN). Always recompute `governor` from live spend+clock at `pre_tool_call` before fencing. Audit the block.

12. **Honest 4 k test (F12).** Rename or rewrite `test_three_worker_batch_parent_stays_small` so it claims what it measures (harvest has no raw page; brief+harvest strings < 4 k). A real P6 proof needs a recorded parent transcript.

13. **Audit economics (F13).** Each run jsonl: token delta with `api_request_id`, fetch increment reason, governor transition, card token estimate vs page chars. Enough for `evals/gates.py` to stop using hand-written `audit.json` for those fields.

14. **One named-gap predicate (F14).** Share `_matches_named_gap` between `policy.py` and `fanout.py`.

15. **HARD write path (F15).** Either narrow HARD writes to `briefs/` + `research/`, or change the spec sentence to the seven-dir allowlist. If Citation Gate would refuse `draft_brief` output, fix the draft, not the gate.

16. **Do not invent knobs.** No per-tier `agent.run_budget_seconds`. No `moa` toolset. No academic MCP. Host-set `delegation.model` stays host-set; say so in the run digest if it is empty ("workers inherit parent — cost warning").

---

## 15. Sentence leftovers (so the walk is complete)

### §3.3 leftover

The table's "Enforcement" column is the only remaining text; each row was walked in §2.3–2.6.

### §3.6 leftover

"Explicit tiers, stated in a cache-safe system-prompt section" — walked. The table — walked. The saturation paragraph — walked. There is no further sentence in §3.6.

### §8 leftover

Every table row walked in §4. Closing sentence about the audit file walked (F13).

### §5.4 leftover (this slice)

`gap_scan` / `claim_verify` / `evidence_read` / `worker_brief` schemas are neighboring. `gap_scan` return keys MATCH the sketch (`saturation`, `unanswered`, `thin`, `conflicts`, `stale`, `recommend`, `new_source_yield`) plus EXTRA `ok`, `sources`. `worker_brief.max_fetches` default 12 MATCHES the sketch. Not a Governor bug: 12 is not derived from remaining `budget.fetches`. **DRIFT, minor** (a depth worker can request 12 fetches on `quick` with 5 left).

### §5.7 leftover (this slice)

Citation Gate, write policy, Evidence Bus intake, bibliography — other auditors. Noted only where they collide with HARD-still-writes (Citation Gate can refuse a HARD write).

### §5.2 `gap_scan` one-liner

> Returns the saturation number.

True as a field. False as the stopping criterion. See F07.

### §5.6 digest example

```
[HDR] run r-7f2 · phase DEPTH · tier deep · budget 41% · saturation 0.18
```

Code (`prompt.digest_text`): same shape, `budget` is **token** percent only (`spend.tokens / budget.tokens`), plus extra lines for governor / open / thin / last / AMBER|RED note. Token-only percent can read GREEN in the digest while fetch ratio is already AMBER. **DRIFT, minor.**

### P8

Walked in §7. The phase is "independently mergeable"; the fixture exists; the acceptance sentence is only half-true.

### §13 / HONEST-LIMITS

> Budget numbers in §3.6 are starting points calibrated to nothing yet. P10 replaces them with measurements.

Code uses those starting points. Honest. P10 fixtures track tokens per A/B source in **hand-written** `evals/fixtures/*/audit.json` (`run_a`: 12000 tokens / 2 A/B / 40 s / 360 s budget). That is not a measurement of the Governor.

---

## 16. Official Hermes notes used (not invented)

From Context7 `/nousresearch/hermes-agent` and `docs/HERMES-FACTS.md` (2026-08-27):

- `pre_api_request` / `post_api_request` are observers. `usage` is on post. Return ignored.
- `pre_tool_call` can block `delegate_task`. First valid `block` wins.
- `pre_tool_call` timeout is fail-closed; other bounded hooks fail open.
- `agent.run_budget_seconds`: optional; 80% one-time wrap-up; **resets on each user message**.
- `compression.proactive_prune_tokens: 48000`, `tail_mode: lean`, `prompt_caching.cache_ttl` in `{5m, 1h}`, `tool_budget.mcp_result_size_chars` are real knobs.
- No `moa` toolset. No invented academic MCP. Path install.

The Governor does not invent a Hermes knob. It uses documented observer hooks plus `pre_tool_call`. That part is clean.

---

## 17. Honest limits of this audit

- No live Hermes session. Hook payload shapes (dict vs `CanonicalUsage`, presence of `total_tokens`, child hook inheritance) are UNPROVEN.
- `llms.txt` fetch timed out; Context7 + HERMES-FACTS were used.
- Sibling slices (Evidence Bus card quality, Citation Gate, MCP facades) were read only where they touch spend or HARD writes.
- `evals/questions.json` mix (4 standard / 6 deep / 2 exhaustive) MATCHES §10; offline runner always creates `tier: "standard"` regardless of the question's tier (`evals/run_offline.py:run_question`). That is a P10/budget DRIFT noted for the closer who owns evals; it means offline "completion" never exercises deep/exhaustive envelopes.

---

## 18. What success looks like for a later closer

A closer for this slice is done when:

1. Crossing 100% tokens **or** fetches **or** tier seconds, through the real increment paths, flips HARD without mutating `run.json` by hand.
2. That transition writes a ledger-only brief to disk even if the model does nothing else.
3. `web_extract` / `delegate_task` stay blocked; `write_file` of that brief stays allowed.
4. Saturation is the compound rule, with a unit test where two off-topic A/B sources do **not** close an unrelated open question.
5. `quick` cannot `delegate_task`.
6. Audit jsonl can explain the last governor transition without a human fixture.

Until then, treat the Budget Governor as a correctly named fence around incomplete meters, and treat `test_governor_forced_overspend` as a policy-unit test, not as proof that HARD never silent-fails.
