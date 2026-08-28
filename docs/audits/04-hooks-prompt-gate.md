# HDR audit 04 — hooks + prompt + gate

**Base:** `main` @ `4019e7cf061c34f6f3d6b74025f66c4f1663aa07`  
**Slice:** hook surface, cache-safe prompt assembly, write policy, Citation Gate, output transform, lifecycle, session reset.  
**Spec:** `docs/HDR-SPEC.md` §§3.1, 4.4, 5.6, 5.7, 13 (plus hook mentions in §3.2–3.4, §4.6, §8).  
**Facts file:** `docs/HERMES-FACTS.md` (hook names, `pre_llm_call`, `transform_*`).  
**Mode:** discovery only. No production code was changed. Fixes are numbered at the end and were **not** applied.

Official Hermes docs were read first via Context7 `/nousresearch/hermes-agent` (hooks catalog, prompt assembly, `_invoke_hook_callback`). Fallback page: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks.

---

## 0. How to read this audit

Classification for every finding:

| Tag | Meaning |
| --- | --- |
| **MATCH** | Implemented, registered, and does the spec job with the official return shape. |
| **GAP** | Spec requires it; code is missing, never fires, or cannot do the job. |
| **DRIFT** | Something exists, but the job, scope, or return shape differs from the spec. |
| **EXTRA** | Code does work the spec did not ask this hook to do. |
| **UNPROVEN** | Cannot be confirmed from this tree + offline tests + official docs alone. Needs a live Hermes loop. |

Severity: **blocker** (the advertised mechanism silently fails or a write/citation gate can be walked around) / **major** (wrong job or porous policy) / **minor** (shape, wording, completeness) / **docs** (README/spec/playbook mismatch only).

Evidence tags reuse the spec’s language: `[DOC]` = official Hermes page; `[INF]` = this audit’s measurement or reading of HDR code; `[UNV]` = not live-probed against a Hermes process.

---

## 1. Verdict

The hook **surface** is complete. `plugin.yaml` `provides_hooks` and `hdr.register` (`agents/research-bot/plugins/hdr/__init__.py:64-78`) register every name in spec §5.7. None of the names are invented. `pre_verify` is correctly **absent**. SOUL.md does not contain mechanical gates. Static HDR contract lives in `register_system_prompt_section`; the per-turn digest is a `{"context": ...}` on the user message, capped in code at 1 200 characters.

The **policy engine** is real and mostly pointed at the right tools. Write allowlist, URL dedupe, AMBER/RED/HARD `delegate_task` / network fences, `curl | sh`, and credential-path blocks all return the official `{action, message}` (or `{action: modify, args}`) shape. The Citation Gate **does** run on `write_file` / `patch` under **both** `briefs/` **and** `research/` (and, more broadly, every allowlisted directory). Chat-only answers bypass it; that is the admitted §13 limit. Offline, `transform_llm_output` does flag uncited statistics when called with a positional `text` argument.

The load-bearing problems in *this* slice:

1. **`transform_llm_output` is wired to the wrong official payload key.** Hermes invokes hooks as `callback(**payload)` when the callback accepts `**kwargs` (`hermes_cli/plugins.py` `_invoke_hook_callback`, `[DOC]`). Official payload key is `response_text`. HDR declares `text`. Calling `transform_llm_output(response_text="…")` raises `TypeError: missing 1 required positional argument: 'text'`. Hermes swallows hook exceptions. The free bibliography **and** the §13 chat-flag mitigation therefore do not run on a live turn. Unit tests hide this by calling the function positionally. **GAP / blocker.**
2. **Citation Gate does not read `claim_verify` / the claim graph.** Spec §3.4 says the gate refuses a brief while an unsupported claim still carries a citation marker. The implementation only checks ledger id resolution and “statistic/date/quantity/quote without `[S#]`”. A sentence `Aliens landed in 2024 [S1].` writes successfully. **GAP / major.**
3. **Citation Gate is scoped to every allowlisted directory, not “the brief directory”.** `notes/scratch.py` containing `YEAR = 2024` and `data/table.json` containing `{"year": 2024}` are refused. Spec §5.7.6 explicitly allows `.py` / `.json` analysis artifacts in those dirs. **DRIFT / major.**
4. **Write-path allowlist is a path-component set intersection, not a directory prefix.** `/tmp/briefs/pwn.py` and `../briefs/x.md` are allowed. **GAP / major.**
5. **`execute_code` “block on effect” is not implemented.** `open('/tmp/x','w').write('hi')` is allowed. `pip install` is a warning, not a block, despite §5.7.6 listing host package installs as a blocked effect. **GAP / major.**
6. **`pre_tool_call` fail-open on exception** (`policy.py:79-80` returns `None`) plus Hermes’ own exception isolation means a thrown gate is a permit. Official *timeout* for `pre_tool_call` is fail-closed; plugin exceptions are fail-open. **DRIFT / major** for a write/citation gate.
7. **Hook store updates are not atomic with their reads.** `run.add_spend` / `query_hashes` / `domain_counts` / `last_batch_ids` do `load_run()` then later `save_run()`. Registry tools and `pre_tool_call` can run concurrently (`ThreadPoolExecutor`, `[DOC]`). Lost updates are possible. **GAP / major** (thread safety).

Everything else in §5.7 exists and is pointed at the named job, with the smaller DRIFT/GAP items listed per hook.

---

## 2. Files actually read

Required:

- `docs/HDR-SPEC.md`
- `docs/HERMES-FACTS.md`
- `agents/research-bot/plugins/hdr/plugin.yaml`
- `agents/research-bot/plugins/hdr/hooks/__init__.py`
- `agents/research-bot/plugins/hdr/hooks/prompt.py`
- `agents/research-bot/plugins/hdr/hooks/policy.py`
- `agents/research-bot/plugins/hdr/hooks/output.py`
- `agents/research-bot/plugins/hdr/hooks/lifecycle.py`
- `agents/research-bot/plugins/hdr/hooks/intake.py`
- `agents/research-bot/plugins/hdr/hooks/subagents.py`
- `agents/research-bot/plugins/hdr/__init__.py`

Also read, because the hooks are not self-contained:

- `hooks/governor.py` (imported and registered as `pre_api_request` / `post_api_request`)
- `runtime.py` (`BRIEF_DIRS`, `INTERCEPTED`, `WRITE_TOOLS`, `NETWORK_TOOLS`, `READ_ONLY_WHEN_HARD`, `estimate_tokens`)
- `store/run.py`, `store/ledger.py`, `store/bus.py`, `store/sanitize.py`, `store/claims.py`
- `tools/citation.py` (`cite_source` used by `transform_llm_output`; `claim_verify` *not* used by the gate)
- `agents/research-bot/SOUL.md`, `README.md`, `INTEGRATION.md`, `config.yaml`
- `docs/HONEST-LIMITS.md`
- `tests/test_hdr_plugin.py` (what is proven vs hidden)

Hermes official (Context7 `/nousresearch/hermes-agent`):

- Hook catalog: `pre_llm_call`, `pre_tool_call`, `post_tool_call`, `transform_tool_result`, `transform_terminal_output`, `transform_llm_output`, `pre_api_request`, `post_api_request`, `api_request_error`, `on_session_start` / `end` / `finalize` / `reset`, `subagent_start` / `stop`, `pre_verify`, `register_system_prompt_section`
- `PluginManager.invoke_hook` / `_invoke_hook_callback` (kwargs binding, fail-open exceptions)
- Prompt assembly: cached system = stable → context → volatile; `pre_llm_call` appends to the **user** message; subagents skip `SOUL.md`

No invented Hermes hook names appear in `provides_hooks` or `register()`.

---

## 3. Registration matrix

`plugin.yaml` `provides_hooks` (lines 29–44) lists 15 names. `register()` registers the same 15, in the same order. `hooks/__init__.py` re-exports all of them. Offline `FakeCtx` after `register(ctx)` recorded exactly:

```
on_session_start, on_session_end, on_session_finalize, on_session_reset,
pre_llm_call, pre_tool_call, post_tool_call, transform_tool_result,
transform_terminal_output, transform_llm_output, pre_api_request,
post_api_request, subagent_start, subagent_stop, api_request_error
```

| §5.7 hook | `provides_hooks` | `register()` | Implementation | Official name? |
| --- | --- | --- | --- | --- |
| `on_session_start` | yes | yes | `lifecycle.on_session_start` | yes `[DOC]` |
| `on_session_end` | yes | yes | `lifecycle.on_session_end` | yes `[DOC]` |
| `on_session_finalize` | yes | yes | `lifecycle.on_session_finalize` → `on_session_end` | yes `[DOC]` |
| `on_session_reset` | yes | yes | `lifecycle.on_session_reset` | yes `[DOC]` |
| `pre_llm_call` | yes | yes | `prompt.pre_llm_call` | yes `[DOC]` |
| `pre_tool_call` | yes | yes | `policy.pre_tool_call` | yes `[DOC]` |
| `post_tool_call` | yes | yes | `policy.post_tool_call` | yes `[DOC]` |
| `transform_tool_result` | yes | yes | `intake.transform_tool_result` | yes `[DOC]` |
| `transform_terminal_output` | yes | yes | `intake.transform_terminal_output` | yes `[DOC]` |
| `transform_llm_output` | yes | yes | `output.transform_llm_output` | yes `[DOC]` |
| `pre_api_request` | yes | yes | `governor.pre_api_request` | yes `[DOC]` |
| `post_api_request` | yes | yes | `governor.post_api_request` | yes `[DOC]` |
| `subagent_start` | yes | yes | `subagents.subagent_start` | yes `[DOC]` |
| `subagent_stop` | yes | yes | `subagents.subagent_stop` | yes `[DOC]` |
| `api_request_error` | yes | yes | `lifecycle.api_request_error` | yes `[DOC]` |
| `pre_verify` | **no** | **no** | none (intentional) | yes `[DOC]`; spec says do not use |

**MATCH** for “hooks exist and are registered under official names.”  
**UNPROVEN** that a live Hermes 0.19.0 process actually dispatches every one of these (CI is structure-only; `evals/smoke/P1-LIVE.md` is cited in the README but was not re-run here).

§4.4 layout vs tree: `governor.py` exists (spec listed it). `lifecycle.py` also owns `api_request_error` (spec table puts that hook in the §5.7 list; the layout comment only names start/end/reset). **MATCH** / docs nit.

---

## 4. Official return shapes vs HDR

Hermes `[DOC]` (hooks catalog + `invoke_hook`):

| Hook | Official return | HDR return | Verdict |
| --- | --- | --- | --- |
| `pre_llm_call` | `{"context": str}` or `str` or `None`; joined and injected on the **user** message | `{"context": text}` or `None` | **MATCH** |
| `pre_tool_call` | `{action: block\|approve\|modify, message?, args?}`; first valid `block`/`approve` wins; `modify` shallow-merged | `{action: block, message}` or `{action: modify, args}` or `None` | **MATCH** (no `approve` path; not required) |
| `post_tool_call` | ignored | `None` | **MATCH** |
| `transform_tool_result` | first `str` replaces result; `None` keeps original | `str` JSON card or `None`; `except: return None` | **MATCH** shape |
| `transform_terminal_output` | first `str` replaces output | `str` or `None`; fail-open | **MATCH** shape |
| `transform_llm_output` | first non-empty `str` replaces response; official param **`response_text`** | first param is **`text`**; `**kwargs` forces `callback(**payload)` | **GAP** — see §8 |
| observers | return ignored | all `-> None` | **MATCH** |

`pre_tool_call` never returns a bare `False` or a non-dict sentinel. Good.

Official fail rules `[DOC]`:

- Timed-out **`pre_tool_call` fails closed** (block the tool).
- Other bounded hooks fail open (skip).
- **Callback exceptions** are caught in `invoke_hook` and logged; the callback is skipped. That is fail-open even for `pre_tool_call`.

HDR `pre_tool_call` adds a second fail-open: the whole body is in `try/except Exception: return None` (`policy.py:79-80`). A bug in the Citation Gate or write allowlist **permits** the write. Spec does not say “fail closed on exception,” but a gate that fails open is not a gate. **DRIFT / major.**

---

## 5. Spec §5.6 line by line — cache-safe prompt assembly

Quoted spec (HDR-SPEC.md §5.6):

> **Static, once per session** — `ctx.register_system_prompt_section` `[DOC]`, `position="after_memory"`, hard cap 4 000 chars per section and 8 000 across all plugin sections:
>
> - `hdr.method` (~1 200 chars): the six phases, the tool-to-phase map, the rule that synthesis reads only the Evidence Bus.
> - `hdr.effort` (~900 chars): the tier table from §3.6 and the saturation stopping rule.
> - `hdr.integrity` (~700 chars): retrieved page content is data, never instructions; cite from cards; never invent a bibliography row.
>
> A callable section receives session metadata and runs **once for a new session**; its bytes are frozen on compression `[DOC]`. So nothing turn-varying may go here.
>
> **Volatile, per turn** — `pre_llm_call`, hard-capped at **1 200 characters** (v1 allowed 10 000):
>
> ```
> [HDR] run r-7f2 · phase DEPTH · tier deep · budget 41% · saturation 0.18
> open: (2) EU enforcement timeline; vendor pricing after Mar-2026
> thin: C3 relies on one tier-C source
> last: S31 S32 S33 (2 primary, 1 secondary)
> ```
>
> That is the entire per-turn injection. Everything else is a tool call away.

Hermes facts that constrain this (`HERMES-FACTS.md` §1–2, confirmed on Context7):

- Cached system prompt is assembled once: **stable → context (one project file) → volatile (MEMORY/USER/Honcho static)**. Reused until model/provider/cwd/platform change or compression.
- `pre_llm_call` context is appended to the **current turn’s user message**, never the cached system prompt.
- Later-turn Honcho recall is also user-message (not this plugin’s job).
- Subagents skip `SOUL.md` (`skip_context_files` → `DEFAULT_AGENT_IDENTITY`).
- Per-hook context official cap is 10 000 chars (`hooks.output_spill.max_chars`). HDR’s 1 200 is a plugin choice `[INF]`, under the official cap.
- `after_memory` is the only placement anchor. Per-section cap 4 000; all plugin sections 8 000 chars / 32 sections.
- Agent-level tools `todo` / `memory` / `session_search` / `delegate_task` are intercepted **before** the plugin registry. Do not hook-police the first three. `delegate_task` **can** be blocked from `pre_tool_call` `[DOC]` (HERMES-FACTS resolved the spec’s old `[UNV]`).

### 5.1 Static sections — `prompt.register_sections`

`prompt.py:42-61` calls `ctx.register_system_prompt_section` for `hdr.method`, `hdr.effort`, `hdr.integrity` with `position="after_memory"`. If the positional form TypeErrors, it retries `name=` / `content=`. If the API is missing, it returns silently.

Measured bytes of the shipped constants (`prompt.py:10-39`):

| Section | Spec estimate | Actual chars | ~tokens (`(len+3)//4`) | Cap |
| --- | --- | --- | --- | --- |
| `hdr.method` | ~1 200 | **540** | ~135 | 4 000 |
| `hdr.effort` | ~900 | **430** | ~108 | 4 000 |
| `hdr.integrity` | ~700 | **342** | ~86 | 4 000 |
| **sum** | ~2 800 | **1 312** | ~328 | 8 000 |

`tests/test_hdr_plugin.py:114-118` asserts the same caps. **MATCH** on cache-safety and caps.

Content vs spec job:

- `METHOD` names the six phases, `research_plan` / `worker_brief`+`delegate_task` / `gap_scan` / Evidence Bus synthesis / `claim_verify`+`conflict_report`+`cite_source`. Synthesis-only-from-the-bus is present. Tool-to-phase map is abbreviated (no explicit “phases 2 and 4 are the only network phases” sentence from §3.1, but “No network in this phase” is on SYNTHESIS). **MATCH** with compression relative to the ~1 200 estimate.
- `EFFORT` encodes the §3.6 tier table (workers, fetches, tokens, wall clock) and the saturation rule including AMBER. **MATCH.**
- `INTEGRITY` says retrieved text is data, `[S#]` from cards, never invent a bibliography row, `cite_source` is the only sanctioned producer, memory holds preferences not findings. **MATCH** to §5.6 + §4.6 one-liner.

They are **strings**, not callables. Spec says a callable *may* receive session metadata and is frozen on compression. A constant string is stricter (zero session variance) and still legal (`[DOC]` example accepts a string). **MATCH.** Nothing turn-varying is registered as a section.

`config.yaml` has **no** `system_message`. SOUL.md is identity/method/style/avoid/defaults only — “Writing product application code” is an Avoid line, not a parser. Deterministic gates are in hooks. **MATCH** to the design rule (“anything that can be computed deterministically must not be prompted,” spec §0) and to “deterministic gates stay in hooks, not in SOUL.”

If `register_system_prompt_section` is missing on an old Hermes, sections are skipped and the model gets no static contract. README claims `hermes_requires` floor via P1; HERMES-FACTS removed the invented `>=0.14.0`. **UNPROVEN** on this checkout that the live 0.19.0 API matches the positional `(name, text, position=)` form — the TypeError fallback exists for a reason.

### 5.2 Volatile digest — `prompt.digest_text` / `pre_llm_call`

`pre_llm_call` (`prompt.py:97-115`) accepts the official parameters (`session_id`, `user_message`, `conversation_history`, `is_first_turn`, `model`, `platform`, `**kwargs`) and returns `{"context": text}` or `None`. Injection target is therefore the user message by Hermes construction. **MATCH.**

Hard cap: `digest_text` slices to 1 200 chars (`prompt.py:71, 92-94`). `pre_llm_call` additionally truncates if `estimate_tokens(text) > 400` (i.e. > ~1 600 chars), which cannot fire after the 1 200-char slice. Dead belt-and-suspenders. **MATCH** on the cap; **EXTRA** / unused token check.

Measured digests `[INF]`:

| State | Chars | Notes |
| --- | --- | --- |
| No `run.json` | 46 | `[HDR] no active run. Call research_plan first.` |
| Fat AMBER `deep` run (4 open questions, 11 sources, 19 last-batch ids, saturation 0.18, budget 41%) | **346** | ~87 tokens. Well under 1 200. |

Fat digest produced:

```
[HDR] run r-81f97a · phase DEPTH · tier deep · budget 41% · saturation 0.18
governor: AMBER
open: (4) EU enforcement timeline after the March ; Vendor pricing changes after March 2026 ; Whether US state AG actions track the EU
thin: S1, S2, S3, S4
last: S1 S2 … S8 (11 sources)
AMBER: no new worker batches. Depth on named gaps only.
```

Walk of the spec example vs implementation:

| Spec line | Implementation | Verdict |
| --- | --- | --- |
| `[HDR] run r-7f2 · phase DEPTH · tier deep · budget 41% · saturation 0.18` | Same template; phase is `.upper()` | **MATCH** |
| `open: (2) …` | `open: (N)` plus first 3 questions truncated to 40 chars | **MATCH** (lossy but capped) |
| `thin: C3 relies on one tier-C source` | `thin:` is up to 4 source **ids** with `tier in {C,D}`, not a claim-id narrative | **DRIFT / minor** |
| `last: S31 S32 S33 (2 primary, 1 secondary)` | `last:` is `last_batch_ids[:8]` plus total source count; **no** primary/secondary breakdown | **DRIFT / minor** |
| AMBER one-liner (§3.3) | Appended when `governor == AMBER` | **MATCH** |
| RED “synthesize now from the ledger” (§3.3) | Appended when `governor in {RED, HARD}` | **MATCH** |

The digest reads `run.json` + `ledger.list_sources`. It does **not** dump corpus text, ledger quotes, or MEMORY/USER blocks. **MATCH** to “Do not dump the corpus into the system prompt” and “That is the entire per-turn injection.”

Dedup: if the digest string is already a substring of `user_message`, return `None` (`prompt.py:111-112`). Prevents stacking on retries. **EXTRA** (useful). Fail-open on exception: `None`. **MATCH** for a directive that must not break the turn.

`conversation_history` / `is_first_turn` / `model` / `platform` are accepted and discarded. Fine.

Does this violate Hermes cache construction? No: static sections are system-prompt; digest is user-message. Honcho static still sits in the volatile *system* tier; HDR does not write there. Subagents skip SOUL; they would still receive plugin sections if Hermes evaluates them for children — **UNPROVEN**. Spec §7.2 says children start blank and skip SOUL; `worker_brief` is supposed to carry the contract. If plugin sections also attach to children, that is extra tokens, not a cache break.

### 5.3 G06 / G25

- **G06** (static contract re-injected every turn via `pre_llm_call`, 10k cap): fixed in construction. Contract is in prompt sections; digest is ≤1 200. **MATCH.**
- **G25** (no effort scaling): tier table is in `hdr.effort` (paid once) and the digest reports the active tier. The *governor* that *enforces* the envelope is `pre_tool_call`, not the prompt. **MATCH** for the prompt half of G25.

---

## 6. Spec §5.7 — hook-by-hook

### 6.1 `on_session_start` — observer

**Spec job:** “init run state, migrate ledger schema, prune corpus past retention.”

`lifecycle.on_session_start` (`lifecycle.py:11-20`):

1. `ledger.init_ledger()` — creates `ledger.json` if missing; `_load_unlocked` migrates `version != 2` via `migrate_v1` and writes it (`ledger.py:92-110, 124-129`).
2. `bus.prune_corpus(corpus_retention_days)` (default 30 from `plugin.yaml` / config).
3. `ledger.mark_corpus_gone` for each pruned digest (clears `corpus` on the ledger row).

Does **not** create `run.json` / `empty_run()`. Run init is `research_plan`. Spec’s “init run state” is therefore only half-done: store is ready, no active run. The no-run digest tells the model to call `research_plan`. **DRIFT / minor** (reasonable), or **MATCH** if “run state” means “plugin store.”

Does **not** write a run summary. Not this hook’s job.

Side effects: filesystem under `plugin-data/hdr/`. Fail-open. Thread safety: `init_ledger` and `prune_corpus` take `bus.lock()`. **MATCH** for migrate + prune.

Official signature: `session_id, model, platform, **kwargs`; return ignored. HDR matches.

### 6.2 `on_session_end` / `on_session_finalize`

**Spec job:** “flush, archive the run, write the run summary.”

`on_session_end` (`lifecycle.py:23-31`): if a run exists, `run.archive_run` copies it to `runs/<run_id>.json` and appends `{event: session_end}` to the audit jsonl. Does **not** delete or empty `run.json`. Does **not** write a separate summary document. “Flush” is just the archive write (atomic via `bus.lock()`).

`on_session_finalize` is an alias of `on_session_end`. Fine if Hermes fires one or both; if it fires both, the archive is written twice (same path, same contents aside from `updated_at` only on `save_run`, which is not called here). **MATCH** / tiny extra write.

**DRIFT / minor:** no dedicated “run summary” artifact. The archived `run.json` *is* the summary.

Official `on_session_end` signature includes `completed`, `interrupted`, `model`, `platform`. HDR accepts `session_id, **kwargs` so extra keys are ignored. **MATCH.**

### 6.3 `on_session_reset`

Not given its own job paragraph in §5.7; it is in the table via layout §4.4 and `provides_hooks`. Official `[DOC]`: fires when a session boundary is crossed or the gateway swaps session keys.

`on_session_reset` (`lifecycle.py:38-43`): `on_session_end` then `ledger.init_ledger()`. **Does not clear `run.json`.** Offline probe: after reset, `run_path().is_file()` is still True and `load_run()` returns the same run; an archive copy exists. A `/new` or gateway reset therefore keeps the previous run as “active.” The next `pre_llm_call` still injects the old digest. **GAP / major** for “session reset.”

### 6.4 `pre_llm_call`

Covered in §5. Registered, official shape, user-message injection, ≤1 200 chars, no corpus dump. **MATCH** (with the minor digest-field DRIFT above).

### 6.5 `pre_tool_call` — policy engine

**Spec job:** “dedupe fence, budget fence, Citation Gate, write policy, arg normalization via `modify`.”  
**Spec order (§5.7 numbered list):**

1. Return `None` for `todo` / `memory` / `session_search`; *may* block `delegate_task` for AMBER/RED.
2. Dedupe `web_extract` / `browser_navigate` (canonical URL already in corpus); near-duplicate `web_search` (normalized hash, 15-minute window).
3. Budget fence per §3.3.
4. Domain denylist + same-domain-N-times soft cap → `modify` query with `-site:`.
5. Citation Gate on `write_file` / `patch` under the brief directory.
6. Write policy v2 + terminal/execute_code effect blocks.

Implementation order in `policy.pre_tool_call` (`policy.py:34-80`): intercepted early-return → `delegate_task` fence → budget fence → dedupe → domain soft cap → write allowlist + citation gate → terminal effect.

Return shape: official `{action, message}` / `{action: modify, args}`. **MATCH.**

#### (1) Intercepted tools

`INTERCEPTED = {todo, memory, session_search, delegate_task}` (`runtime.py:30`).  
`if name in INTERCEPTED and name != "delegate_task":` log-observe `memory`, then `return None` (`policy.py:44-51`).

Offline: `todo` / `memory` / `session_search` all return `None`. Memory appends `memory-observe` to the audit when a run exists. **MATCH** to §4.6 and HERMES-FACTS (“block would be ineffective”).

`delegate_task` continues into `_delegate_fence`. GREEN: allow. RED/HARD: block. AMBER: allow only if `goal|prompt|task|instruction` fuzzy-matches `named_gaps` or `open_questions`. Tests cover AMBER block vs named-gap allow (`test_hdr_plugin.py:393-426`). **MATCH** to §3.3 and the resolved `[DOC]` that `pre_tool_call` can block `delegate_task`.

This audit does **not** hook-police `todo` / `memory` / `session_search`. Correct.

#### (2) Dedupe fence

`_dedupe_fence` (`policy.py:174-193`): `web_extract` / `browser_navigate` canonicalize URL; `bus.corpus_exists_for_url`; block with `Already retrieved as {sid} — read_file {corpus} or call evidence_read src={sid}`. Matches the spec’s example wording. Tested (`test_dedupe_and_citation_gate`). **MATCH.**

`web_search` goes to `_query_dedupe` (`policy.py:196-214`): lowercase/whitespace-normalized query, 15-minute window in `run.json` `query_hashes`, then `save_run`. **MATCH** to “near-duplicate search queries … 15-minute window.” Race: see §10.

No dedupe on `docs_query` / `scholar_search` / `archive_lookup` / `x_search`. Spec only named `web_extract` / `browser_navigate` / search queries. **MATCH.**

#### (3) Budget fence

`_budget_fence` (`policy.py:158-171`) + `_delegate_fence`:

| Governor | Spec §3.3 | Code | Verdict |
| --- | --- | --- | --- |
| GREEN <60% | normal | no-op | **MATCH** |
| AMBER ≥60% | block new `delegate_task` batches; depth on named gaps; digest note | `_delegate_fence` + digest line | **MATCH** |
| RED ≥85% | block all network tools; digest “synthesize now” | blocks `NETWORK_TOOLS`; digest line | **MATCH** |
| HARD ≥100% or wall clock | block everything except `read_file`, ledger tools, and `write_file` under the brief path | blocks anything not in `READ_ONLY_WHEN_HARD` | **DRIFT** — set is wider than spec |

`NETWORK_TOOLS` (`runtime.py:31-43`): `web_search`, `web_extract`, `browser_navigate`, `browser_snapshot`, `x_search`, `docs_query`, `resolve_library`, `scholar_search`, `archive_lookup`. **MATCH** for “network tools.” `terminal` / `execute_code` are not in that set, so RED still allows curl-via-terminal. **GAP / major** relative to “block all network tools” if the model uses `terminal` as a fetch path (the web-fallback skill does exactly that).

`READ_ONLY_WHEN_HARD` (`runtime.py:46-61`) includes spec’s `read_file`, ledger tools, `write_file`, `patch`, **plus** `research_plan` and `worker_harvest`. `write_file`/`patch` are allowed through the HARD fence and then still hit the path allowlist + Citation Gate. Offline: HARD `web_extract` blocked; HARD `src/a.py` blocked by allowlist; HARD `briefs/a.md` with `[S1]` allowed; HARD `research_plan` allowed (hook returns `None`). **DRIFT / minor** on the extra names; **MATCH** that brief-path writes still work.

Wall-clock: `governor_state` uses `spend.seconds / budget.seconds`. Neither `pre_api_request` nor `post_api_request` increments `seconds`. HARD-from-clock is therefore **UNPROVEN** / likely **GAP** unless something else calls `add_spend(seconds=…)`. (Governor-slice territory; it affects this fence.)

Token accounting: `pre_api_request` adds `approx_input_tokens` (or `usage.prompt_tokens`); `post_api_request` adds `total_tokens` or `output_tokens`. If both fire with overlapping counts, spend is inflated and the fence trips early. **UNPROVEN** without a live usage payload; flag as **DRIFT / major** risk for this slice because `pre_tool_call` trusts `run.json.governor`.

#### (4) Domain denylist + soft cap

`_domain_soft_cap` (`policy.py:217-250`):

- If `url` host is in `setting("domain_denylist")`: **`block`**, not `modify`. Spec said denylist *and* soft cap “→ `modify` the query to add `-site:` exclusions rather than blocking outright.” Blocking a denylisted extract URL is defensible; the spec sentence still asked for modify. **DRIFT / minor.**
- Soft cap: if `run.domain_counts[host] >= DOMAIN_SOFT_CAP` (4) and the tool is `web_search`, return `{action: modify, args: {query: query + " -site:…"}}`. Tested (`test_domain_soft_cap_modifies_search`) by **stuffing** `domain_counts`. Production increment of `domain_counts` happens only in `transform_tool_result` on the extract-like path (`intake.py:156-161`), not on `web_search` hits. Soft cap may never trip during a search-only burst. **GAP / minor** (or **UNPROVEN** in a live mixed run).

#### (5) Citation Gate — see §7

#### (6) Write policy + terminal — see §8

`pre_tool_call` side effects: audit lines (memory, scaffold), `save_run` (query hashes), no mutation of tool results. **MATCH** for a directive hook.

### 6.6 `post_tool_call` — observer

**Spec job:** “audit log, per-tool latency, fetch counter.”

`policy.post_tool_call` (`policy.py:83-101`): `bus.append_audit({tool, duration_ms})`; if `tool_name in NETWORK_TOOLS`, `run.add_spend(fetches=1)`. Tested (`test_fetch_counter_and_index_search`). Return ignored. Official signature matched.

Not a per-tool latency *histogram* — just one audit line per call. **MATCH** if “per-tool latency” means “log duration_ms”; **DRIFT / docs** if a dashboard was implied.

Blocked tools never reach `post_tool_call`. Spec §5.5 wants “every tool call … block decision” in `audit/<run_id>.jsonl`. Block decisions from `pre_tool_call` are **not** written (except scaffold-warning and memory-observe). **GAP / minor.**

### 6.7 `transform_tool_result` — Evidence Bus

**Spec job (§5.7 + §3.2):** after `post_tool_call`, before conversation append; first string replaces the result; fail open; intercept `web_extract`, `web_search`, `docs_query`, `browser_snapshot`, `x_search`; canonicalize; write corpus; extract metadata; score; up to three quote spans; replace with Evidence Card; wrap untrusted content; record `suppressed[]` in the audit, do not silently delete.

`INTAKE_TOOLS` (`intake.py:13-15`) is exactly that set. **MATCH.** `browser_navigate` is not in the set (spec list omits it too).

`transform_tool_result` (`intake.py:73-164`): fail-open `except: return None`. Tested with a `Boom` object (`test_evidence_bus_card_and_byte_exact`). Card token budget ≤400 via `estimate_tokens` (chars/4). 40k-char page test asserts card ≤400 tokens and byte-exact corpus. **MATCH** to P3 acceptance and §3.2 payoff.

Untrusted wrap: `sanitize.wrap` (`sanitize.py:23-45`) adds an envelope and strips ignore-previous / role headers / fenced instruction blocks / hidden-text into `suppressed[]`, audited at `intake.py:147-148`. The **corpus stores the raw `text`**, not the wrapped body (`write_corpus(text, …)`). The **model-visible result is the card**, which has `"untrusted": true` but not the envelope text. Spec: “Wrap every retrieved body in an explicit untrusted-content envelope.” The body that would have entered context is *replaced*, so the envelope never reaches the model on the happy path. Fail-open returns the original unwrapped result. Search-hit cards include raw snippets with **no** `sanitize.wrap`. **DRIFT / minor** on envelope placement; **GAP / minor** on search snippets.

`read_more` on the card is `evidence_read src=…`, not `read_file path=… offset=…` as in the §3.2 JSON example. **DRIFT / docs.**

Side effects: ledger insert, corpus write, `last_batch_ids`, `domain_counts`, audit. Concurrent with other tools — see §10.

### 6.8 `transform_terminal_output`

**Spec job:** “collapse huge `curl`/`grep` dumps to head + summary before the terminal cap.”

`intake.transform_terminal_output` (`intake.py:167-181`): if `len(output) < 4000`, `None`; else 40-line head + char/line/url counts. Does **not** inspect the command (and the signature is `output, **kwargs`, so `command` is available in kwargs but unused). Collapses **any** large dump, not only curl/grep. Official fires only inside the terminal tool, before the final cap — so the hook is in the right place. **MATCH** / slight **EXTRA** (all commands, not just curl/grep).

`execute_code` output is **not** transformed (official hook is terminal-only). Huge Python prints can still flood context up to `tool_output.max_bytes`. **DRIFT / minor** vs a literal reading of “dumps”; not a spec miss if the hook name is terminal-specific.

Official signature includes `command, output, returncode, task_id, env_type`. HDR’s `output` + `**kwargs` binds correctly under `callback(**payload)`. **MATCH** (unlike `transform_llm_output`).

### 6.9 `pre_api_request` / `post_api_request`

**Spec job:** Budget Governor accounting (`approx_input_tokens`, `usage`). Enforcement is in `pre_tool_call`.

`governor.py`: both are observers, fail-open, `add_spend(tokens=…)`. Official payloads documented. **MATCH** as observers. Double-count / missing wall-clock: §6.5. Not invented names.

### 6.10 `subagent_start` / `subagent_stop`

**Spec job:** start stamps `child_subagent_id → open-question` into `run.json`; stop reconciles child findings, counts child tool calls, marks the mandate answered/failed.

`subagents.subagent_start` (`subagents.py:10-28`): writes `children[id] = {status: running, task, open_question}`. `open_question` is `kwargs.get("open_question") or task`. Official start payload may not include `open_question`; then the whole task string is stored. **MATCH** / **UNPROVEN** that Hermes passes a usable `task`.

`subagent_stop` (`subagents.py:31-52`): sets `status` to `done`/`failed`, copies `kwargs["tool_calls"]`, audits. Does **not** harvest findings (that is `worker_harvest`). Does **not** remove or mark the corresponding `open_questions[]` entry answered. **DRIFT / major** on “mark the mandate answered/failed” if that meant the plan’s open-question list; **MATCH** if it only meant the `children` node.

Official: `subagent_start` cannot block; use `pre_tool_call` for delegation. HDR start/stop return `None`. **MATCH.**

### 6.11 `transform_llm_output` — see §8.1 and §9

### 6.12 `api_request_error`

**Spec job:** “classify provider failures into the run audit.”

`lifecycle.api_request_error` (`lifecycle.py:46-54`): writes `{event: api_request_error, error, detail: str(kwargs)[:400]}`. No taxonomy (timeout / 429 / auth / context-length). **DRIFT / minor** (“log” ≠ “classify”). Fail-open. Official: return ignored.

---

## 7. Citation Gate — does it actually run on briefs/ and research/?

### 7.1 Spec

§5.7.5:

> on `write_file` / `patch` where the path is under the **brief directory**, parse the content for claim sentences and `[S#]` markers. Block if a marker is unresolvable in the ledger, or if a sentence containing a statistic, date, quantity, or quoted phrase carries no marker. The block message lists exact offending sentences.

§3.4:

> A claim with no exact span in any corpus file is reported `unsupported`, and the Citation Gate (§5.7) refuses to let the brief be written while an unsupported claim carries a citation marker.

§13 (honest limit):

> `pre_verify` does not fire for markdown-only turns `[DOC]`. The Citation Gate is a `pre_tool_call` block on the **brief write**, so a user who reads the answer straight out of chat without a file write bypasses it. Mitigation: `transform_llm_output` flags uncited statistics inline.

This audit treats the chat bypass as an **admitted limit**, not a secret gap — and then checks whether the file-write gate actually runs, and whether the mitigation hook can fire.

### 7.2 What the code does

Trigger: `name in WRITE_TOOLS` where `WRITE_TOOLS = {write_file, patch}` (`runtime.py:44`). Then `_write_allowlist` then `_citation_gate` (`policy.py:67-73`).

`_citation_gate` (`policy.py:277-298`):

1. Path must pass `_path_allowed` (any `Path.parts` member in `BRIEF_DIRS`).
2. Content from `content` / `new_string` / `text`.
3. Every `[S#]` must be in `ledger.list_sources()` (**all runs**, not the current `run_id`).
4. Every sentence matching `_STAT_RE` (percent, year 19xx/20xx, grouped thousands, curly/straight quotes) must also contain `[S#]`.
5. Block message: `Citation Gate refused this brief:` + up to 8 offenders.

`BRIEF_DIRS = {notes, research, briefs, findings, citations, sources, data}` (`runtime.py:27-29`).

### 7.3 Offline measurements `[INF]`

| Write | Result |
| --- | --- |
| `write_file` `briefs/out.md` “Growth was 12% last year.” | **block** (unmarked stat) |
| `write_file` `research/note.md` same text | **block** (same message) |
| `patch` `research/x.md` `new_string="The rate was 12%."` | **block** |
| `write_file` `briefs/ok.md` “Growth was 12% [S1].” with S1 in ledger | **allow** |
| `write_file` `briefs/u.md` “Aliens landed in 2024 [S1].” (no span check) | **allow** |
| `write_file` `notes/scratch.py` `print(1)` | **allow** (no stat regex) |
| `write_file` `notes/scratch.py` `YEAR = 2024` | **block** |
| `write_file` `data/table.json` `{"year": 2024}` | **block** |
| Chat-only (no write) | gate never runs — admitted §13 limit |

**The gate runs on `briefs/` and on `research/`, and also on every other allowlisted directory, for both `write_file` and `patch`.** That answers the slice question: it is not a no-op, and it is not briefs-only.

### 7.4 Classification

| Check | Verdict |
| --- | --- |
| Exists, registered, official `{action, message}` | **MATCH** |
| Fires on `briefs/` writes | **MATCH** (tested in `test_dedupe_and_citation_gate` and here) |
| Fires on `research/` writes | **MATCH** (measured; no unit test named for this path) |
| Fires on `patch` | **MATCH** (measured) |
| Unresolvable `[S#]` | **MATCH** (`[S99]` test) |
| Unmarked statistic / date / quantity / quote | **MATCH** for stats/dates/quotes in prose |
| Unsupported-but-cited claims (§3.4) | **GAP / major** — never calls `claim_verify` or `claims` |
| Scoped to “brief directory” only | **DRIFT / major** — all `BRIEF_DIRS`; blocks legitimate `notes/` `.py` and `data/` `.json` the write policy promised to allow |
| Chat-only bypass | **MATCH** to admitted §13 limit |
| Mitigation `transform_llm_output` flags uncited stats | **MATCH** when called as `transform_llm_output(text)`; **GAP / blocker** on a live Hermes turn (wrong kwarg) — §8.1 |
| `pre_verify` not used | **MATCH**; README + `HONEST-LIMITS.md` + profile README record the limit (**MATCH** / docs) |
| Ledger scope | **DRIFT / minor** — any historical `S#` satisfies the marker, not just this run |
| Message always says “brief” | **DRIFT / docs** even when the path is `notes/` or `data/` |

Honest-limit wording in output.py:49 is accurate (“Citation Gate only fires on brief writes”) but **over-narrow** relative to the code (it also fires on `research/`, `notes/`, …). **DRIFT / docs.**

---

## 8. Write policy (research-only)

### 8.1 Allowlist

Spec §5.7.6:

> Allow writes under `notes/ research/ briefs/ findings/ citations/ sources/ data/`.  
> Allow any extension inside those directories, including `.py` and `.json`.  
> Block writes **outside** those directories entirely (allowlist, not denylist).

`_path_allowed` (`policy.py:253-259`): `bool(set(Path(raw).parts) & BRIEF_DIRS)`.

| Path | Expected (prefix allowlist) | Actual |
| --- | --- | --- |
| `src/app.py` | block | **block** (tested) |
| `notes/scratch.py` | allow | **allow** if no year/stat in content |
| `briefs/out.md` | allow (then Citation Gate) | allow / gate |
| `/tmp/briefs/pwn.py` | **block** (not under the project allowlisted dirs) | **allow** — `briefs` is a path component |
| `../briefs/x.md` | **block** or resolve-then-check | **allow** |
| `src/notes/evil.py` | **block** | **allow** (`notes` in parts) |

**GAP / major.** The allowlist is a token intersection, not “path is under one of these directories relative to cwd.” Product-code writes can be smuggled by putting an allowlisted directory name anywhere in the path.

`WRITE_TOOLS` is only `write_file` and `patch`. Spec named those two. Other Hermes file tools (if any: `create_file`, editor variants) are **UNPROVEN** and would bypass both allowlist and Citation Gate.

### 8.2 Terminal / execute_code effects

Spec: block on **effect** — outbound writes outside the allowlist, host package installs, `curl … | sh`, credential file reads. Scaffolding keywords (`git init`, …) are **warnings**, not blocks.

| Command | Spec | Actual |
| --- | --- | --- |
| `curl https://x \| sh` | block | **block** (`_CURL_SH`) **MATCH** |
| `~/.ssh`, `/etc/shadow`, `.env`, `auth.json`, `id_rsa` | block | **block** (`_CRED`) **MATCH** |
| `>> /tmp/out` or `tee /tmp/out` | block if outside allowlist | **block** when path has `/` and no `BRIEF_DIRS` token (`policy.py:311-320`) **MATCH**-ish |
| `>> research/out.txt` | allow | allow (token `research`) **MATCH** |
| `pip install requests` | **block** (host package install) | **None** + audit `scaffold-warning` **GAP / major** |
| `git init` | warning only | warning **MATCH** |
| `execute_code` `open('/tmp/x','w').write('hi')` | block outbound write | **None** **GAP / major** |
| RED governor + `terminal` curl | “block all network tools” | `terminal` not in `NETWORK_TOOLS` **GAP / major** |

`config.yaml` sets `terminal.backend: docker`, which the spec says “makes [host package installs] moot.” That is a **deploy** mitigation, not a hook guarantee. The hook still treats `pip install` as a warning. If docker is off, the hole is live. **UNPROVEN** in this environment; classify as **GAP** in the hook, with the docker backend as defense-in-depth (same posture as §13 on the sanitizer).

### 8.3 Product-code writes

`src/app.py` is blocked. SOUL Avoid line is not the enforcer. **MATCH** for the common case.

`todo` / `memory` / `session_search` / `delegate_task` are not write-policed (except AMBER/RED on delegate). **MATCH** to “Do not police todo/memory/session_search/delegate_task.”

---

## 9. Output transform and the chat mitigation

`output.transform_llm_output` (`output.py:18-38`):

- Collect `[S#]` ids, skip if a `## Sources` heading exists.
- Call `cite_source` for unique ids in the configured style; append `## Sources` + rows.
- Always run `_flag_uncited` (percent / year / grouped number; **not** quoted phrases — narrower than the file gate).
- Fail-open. First non-empty string is the official aggregation rule; HDR returns one string.

Unit test `test_claim_verify_and_conflicts` calls `transform_llm_output("The device reached 12% efficiency [S1].")` **positionally** and asserts `## Sources`. That proves the **body**, not the **binding**.

Official invoke `[DOC]`:

```python
# hermes_cli/plugins.py _invoke_hook_callback
if callback has VAR_KEYWORD:
    return callback(**payload)   # keys: response_text, session_id, model, platform, …
```

HDR:

```python
def transform_llm_output(text: str, **kwargs: Any) -> str | None:
```

Measured:

```
transform_llm_output(response_text="The device reached 12% [S1].")
→ TypeError: missing 1 required positional argument: 'text'
```

Hermes `invoke_hook` catches that, logs a warning, and skips. **The bibliography does not append. The uncited-statistic banner does not append.** The §13 mitigation is dead on a live turn.

Classification: **GAP / blocker.** Severity is blocker because (a) §5.7 lists this as the zero-token bibliography (token-economics table §8), and (b) it is the only mechanical backstop for chat-only answers.

Fix (not applied): rename `text` → `response_text`, or `def transform_llm_output(response_text: str = "", text: str = "", **kwargs)` and read `response_text or text`. Add a unit test that calls it with `response_text=`.

`_flag_uncited` when invoked correctly: measured chat string `Revenue grew 12% in 2024.` gained the banner that names the admitted limit. **MATCH** to §13 mitigation *as a function*. Banner is **EXTRA** relative to §5.7’s bibliography-only paragraph, but **MATCH** to §13.

---

## 10. Thread safety

Spec §4.4: “registry tools run on a thread pool `[DOC]`. Every store write takes a lock and writes atomically.” Agent-loop fact: multiple `tool_calls` → `ThreadPoolExecutor`; `pre_tool_call` therefore can overlap.

What is locked:

- `ledger.add_source` / `init_ledger` / `mark_corpus_gone` — `bus.lock()`
- `bus.write_corpus` / `append_audit` / `prune_corpus` — `_LOCK`
- `run.save_run` / `archive_run` — `bus.lock()` around the write

What is **not** locked across read-modify-write:

```
run.add_spend:     data = load_run()          # unlocked
                   mutate spend
                   return save_run(data)      # lock only the write

_query_dedupe:     current = run.load_run()
                   seen = current.setdefault("query_hashes", {})
                   seen[key] = now
                   run.save_run(current)

intake._note_batch / domain_counts: load (via caller), mutate, save_run
```

Two concurrent `post_tool_call` + `post_api_request` can drop a fetch or a token increment. Two concurrent searches can drop a query hash. **GAP / major.**

`runtime._ctx` is process-global, set once in `register`. Read-only after that. **MATCH** for ctx.

Plugin **tool** handlers were not the focus of this slice; the eight-thread ledger test (`test_eight_thread_writes`) only covers `ledger.add_source`. It does **not** cover hook RMW on `run.json`.

---

## 11. Lifecycle vs durable state (§5.5)

| Artifact | Who writes | Hook involvement |
| --- | --- | --- |
| `run.json` | `research_plan`, fences, intake, governor, subagents | start does not create; reset does not clear |
| `runs/<id>.json` | `on_session_end` / finalize / reset | archive only |
| `ledger.json` | intake, tools, start (init/migrate) | **MATCH** |
| `corpus/` | intake | prune on start **MATCH** |
| `audit/<id>.jsonl` | post_tool_call, governor, memory observe, scaffold, subagents, api errors, suppressed | **GAP** — block decisions from `pre_tool_call` usually absent |
| `claims.json` | tools, not the Citation Gate | **GAP** vs §3.4 |

---

## 12. Spec §3.1 / §4.4 / §13 hook mentions

**§3.1 loop.** Hooks do not implement the loop; they constrain it. Synthesis-from-ledger is a prompt-section rule plus RED/HARD network fence — not a phase machine that forbids `web_extract` during `phase==synthesis` while GREEN. A GREEN synthesizer can still fetch. **GAP / major** relative to “Phase 5 reads only the Evidence Bus,” if that was meant to be mechanical. Spec §3.1 is a flowchart for the *model*; the mechanical pieces named for hooks are §3.2–3.3 and §5.7. Classify as **UNPROVEN / design**: the digest *reports* `phase`, it does not *enforce* it.

**§4.4.** Layout matches. Concurrency claim is only half-true (ledger yes, run.json RMW no). Memory observer present.

**§13.** README and `docs/HONEST-LIMITS.md` copy the `pre_verify` / chat-bypass paragraph. **MATCH / docs.** The mitigation hook is broken on official kwargs (this audit’s blocker). Children/`HERMES_HOME` and MoA-as-provider are out of slice except: no `moa` toolset in `config.yaml` (STOP honored).

---

## 13. Tests: what they prove and what they hide

`tests/test_hdr_plugin.py` (offline, FakeCtx):

| Test | Proves | Hides |
| --- | --- | --- |
| `test_register_surfaces` | all three sections; `pre_tool_call` and `on_session_reset` registered; caps | does not assert the full 15-hook list (only samples) |
| `test_dedupe_and_citation_gate` | URL dedupe; unresolvable `[S99]` on `briefs/` | no `research/` path; no unsupported-cited claim; no `response_text` binding |
| `test_write_allowlist` | `src/app.py` block; `notes/scratch.py` without a year | `/tmp/briefs/…`; year in notes; `execute_code` writes |
| `test_plan_digest_and_gap_scan` | digest ≤1200 after `research_plan` | field-level match to the spec example |
| `test_claim_verify_and_conflicts` | bibliography append via **positional** call | live kwargs |
| `test_governor_forced_overspend` | HARD blocks extract; brief write of a drafted cited brief allowed | RED+terminal; clock |
| `test_amber_named_gap_depth` | AMBER `delegate_task` block vs named gap | live Hermes honoring the block (HERMES-FACTS `[DOC]` says it does) |
| `test_domain_soft_cap_modifies_search` | modify shape | natural increment of `domain_counts` |
| `test_eight_thread_writes` | ledger inserts | hook/run.json races |
| `test_evidence_bus_card_and_byte_exact` | card size, byte-exact corpus, fail-open | search-snippet sanitization |

No test calls `transform_llm_output(response_text=…)`. No test for session reset clearing `run.json`. No test that Citation Gate consults `unsupported`.

---

## 14. Per-hook scoreboard (quick)

| Hook | Registered | Implemented | Spec job | Official shape | Side effects | Threads | Class | Sev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `on_session_start` | yes | yes | migrate + prune; run not created | observer | ledger/corpus | locked | **MATCH** (run-init DRIFT minor) | minor |
| `on_session_end` | yes | yes | archive; no separate summary | observer | archive + audit | locked write | **DRIFT** | minor |
| `on_session_finalize` | yes | alias of end | same | observer | same | same | **MATCH** | — |
| `on_session_reset` | yes | yes | does not clear active run | observer | archive + init ledger | locked write | **GAP** | major |
| `pre_llm_call` | yes | yes | ≤1200 user-message digest | `{context}` | reads run/ledger | read-mostly | **MATCH** | — |
| `pre_tool_call` | yes | yes | policy engine; holes in path/effect/citation-unsupported; fail-open except | `{action,message}` / `modify` | run.json, audit | RMW race | **DRIFT**+**GAP** | blocker/major (see list) |
| `post_tool_call` | yes | yes | audit + fetch++ | ignored | audit, spend | RMW race | **MATCH**/DRIFT | minor |
| `transform_tool_result` | yes | yes | Evidence Bus; envelope/search nits | `str\|None` | corpus, ledger, run | locked + RMW | **MATCH** | minor nits |
| `transform_terminal_output` | yes | yes | collapse large dumps | `str\|None` | none | n/a | **MATCH** | — |
| `transform_llm_output` | yes | yes | bibliography + chat flag | **wrong param name** | cite_source read | n/a | **GAP** | **blocker** |
| `pre_api_request` | yes | yes | token spend | ignored | spend | RMW | **MATCH**/UNPROVEN double-count | major risk |
| `post_api_request` | yes | yes | token spend | ignored | spend | RMW | same | major risk |
| `subagent_start` | yes | yes | child map | ignored | run.json | RMW | **MATCH** | — |
| `subagent_stop` | yes | partial | no mandate/open_question close | ignored | run.json | RMW | **DRIFT** | major |
| `api_request_error` | yes | log only | no classify | ignored | audit | locked append | **DRIFT** | minor |
| `pre_verify` | no | no | correctly unused | — | — | — | **MATCH** | — |

**EXTRA:** digest already-in-user-message short-circuit; token estimate belt; `research_plan` on HARD allowlist; terminal collapse for all commands; chat-flag banner (wanted by §13).  
No extra / invented hook names.

---

## 15. Numbered fix list (do not apply)

1. **Rename `transform_llm_output`’s first parameter to `response_text`** (or accept both). Add a test that invokes it as Hermes will: `transform_llm_output(response_text=..., session_id="", model="", platform="")`. Until this lands, treat bibliography + chat-flag as **not shipping**. (blocker)

2. **Make `pre_tool_call` fail closed on unexpected exceptions** when the intended action was a write or a network fetch: return `{action: block, message: "HDR policy error"}` instead of `None`. Keep fail-open for observers/transforms. (major)

3. **Citation Gate + claim graph:** before allowing a brief write, parse cited claims (or the sentences that carry `[S#]`) and refuse while `claim_verify` (or stored `claims` status) is `unsupported`. Quote the offending sentence in the block message, as spec §3.4 / §5.7.5. (major)

4. **Scope the Citation Gate to brief-class paths** (`briefs/` and, if product-intent stays, `research/` + `findings/`). Do **not** run the statistic regex on `notes/*.py`, `data/*.json`, `citations/` dumps. Align `_flag_uncited` copy with the actual scope. (major)

5. **Rewrite `_path_allowed` as a resolved-prefix check** against cwd (and/or `plugin-data`) for the seven allowlisted directories. Reject `/tmp/briefs/…`, `../briefs/…`, `src/notes/…`. (major)

6. **Block host-package-install effects** (`pip install`, `npm i`, `apt-get install`) in `_terminal_effect`, not as scaffold warnings. Keep `git init` as warning. (major)

7. **`execute_code` write/network policy:** parse or conservatively block `open(..., "w")` / `pathlib.write_*` / `requests.get` / `urllib` to hosts/paths outside the allowlist. Today the effect fence is shell-redirect regex only. (major)

8. **Put `terminal` (and maybe `execute_code`) on the RED network fence**, or detect outbound fetch commands, so “block all network tools” cannot be walked around via the fallback skill’s curl. (major)

9. **`on_session_reset` must retire the active run:** archive, then remove or replace `run.json` with `empty_run()` (or `None`), so the next digest is `no active run`. (major)

10. **Atomic `run.json` RMW:** `add_spend`, query-hash, domain-count, and `last_batch_ids` updates must load-mutate-save under `bus.lock()` (single critical section). Add a concurrent hook test alongside `test_eight_thread_writes`. (major)

11. **Log every `pre_tool_call` block/modify** to `audit/<run_id>.jsonl` (`event: policy-block`, tool, message). Satisfies §5.5. (minor)

12. **Tighten the digest** to the spec example: thin line as claim-id narrative if available; last-batch kind counts (`N primary, M secondary`). Still hard-cap 1 200. (minor)

13. **`subagent_stop`:** if `open_question` is known, mark that mandate answered/failed on `run.json` (and leave harvest to `worker_harvest`). (major)

14. **`api_request_error`:** classify into a small enum (`rate_limit`, `auth`, `timeout`, `context`, `other`) in the audit row. (minor)

15. **Do not double-count tokens** in `pre_api_request` + `post_api_request`. Prefer `post` `usage.total_tokens` as source of truth, or add only completion tokens on post. Increment `spend.seconds` from wall clock or Hermes budget remaining if the payload has it. (major; shared with governor slice)

16. **Increment `domain_counts` on search-hit intake** (or on `pre_tool_call` of extract), so the `-site:` modify can fire without a test harness stuffing the dict. (minor)

17. **Sanitize search snippets** before they land on cards; keep fail-open. (minor)

18. **Unit tests to add (not added here):** `research/` gate; `/tmp/briefs` deny; notes `.py` with a year allowed if gate is re-scoped; `execute_code` write; `pip install` block; `transform_llm_output(response_text=)`; reset clears run; concurrent `add_spend`; unsupported `[S#]` brief.

19. **Docs only:** PROFILE-PLAYBOOK.md still describes v1 “blocks product-code writes and scaffolding terminal” and “`pre_llm_call` injects the contract + digest.” Out of this PR’s file set; call out so the playbook is not used as v2 truth. (docs)

20. **Do not** add `pre_verify`. Do not invent hook names. Do not move these gates into SOUL.

---

## 16. What this audit did not do

- No live `hermes` CLI conversation, so dispatch of hooks inside 0.19.0 is `[UNV]` except where official docs + `_invoke_hook_callback` make the kwargs binding certain.
- No measurement of official `hooks.output_spill` truncation on a 1 200-char digest (unnecessary; under 10k).
- No child-session proof that plugin prompt sections are omitted (subagents skip SOUL `[DOC]`; plugin sections **UNPROVEN**).
- Did not implement any fix. Did not refactor. Production tree untouched except this audit file.

---

## 17. Sources for official shapes

- https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- Context7 `/nousresearch/hermes-agent`: `PluginManager.invoke_hook`, `_invoke_hook_callback`, hook APIDOCs
- `docs/HERMES-FACTS.md` (probe date 2026-08-27)
- `docs/HDR-SPEC.md` @ `4019e7cf`
