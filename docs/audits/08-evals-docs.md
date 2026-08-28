# HDR audit 08 — evals + docs

Base: `main` @ `4019e7cf061c34f6f3d6b74025f66c4f1663aa07` (`research-bot HDR v2 — Hermes Deep Research`).

Scope: Evaluation (§10), build order P0–P11 (§11), honest limits (§13), gap register (§1.1), and every user-facing / factory doc that still describes v1 or the wrong plugin name.

This is discovery only. No production code was changed except this file.

Offline unit tests on this checkout: `python3 -m unittest tests.test_hdr_eval_gates tests.test_hdr_plugin -v` — 18/18 OK in 0.185s. That is structure + FakeCtx. It is not a live Hermes run.

---

## How to read this review

Classification:

| Tag | Meaning |
| --- | --- |
| **MATCH** | Spec / official STOP / shipped code or docs agree. |
| **GAP** | Spec or official fact requires it. Main does not have it. |
| **DRIFT** | Main has something. It contradicts the spec, an official STOP, or another shipped file. |
| **EXTRA** | Main ships more than the spec asked for. Harmless unless it teaches the next profile the wrong thing. |
| **UNPROVEN** | Code or a fixture exists. The live acceptance the spec named was not recorded on Hermes 0.19.0. |

Severity:

| Severity | Meaning |
| --- | --- |
| **blocker** | A later profile, or a merge-gate claim, will be wrong if this stays. |
| **major** | Acceptance is weaker than the spec, or a user-facing doc still teaches v1. |
| **minor** | Incomplete, but a careful reader can recover. |
| **docs** | Copy only. No runtime effect unless someone follows it. |

Official STOPs that change acceptance (from `docs/HERMES-FACTS.md` and the task brief):

1. No `moa` toolset. P1 `/tools list` must not require `moa`. MoA is provider `moa`.
2. Path install only. Do not invent a repo-root profiles index.
3. No `hermes plugins doctor` on 0.19.0.
4. No invented academic MCP (`openalex`, `pubmed`, `wayback` as first-party Hermes servers).

Profile name is `research-bot`. Plugin and toolset are `hdr`. Never name a toolset or plugin `army` or `army-runtime`.

ISO 24495-1 applies to user-facing copy. Point first. One idea per sentence. Common words. Keep official Hermes terms (skill, tool, plugin, MCP, SOUL, profile) and define them on first use.

---

## 1. Spec quotes this slice owns

### §10 Evaluation — the thing v1 has none of

`docs/HDR-SPEC.md` lines 781–801:

> Structure-only CI is not evidence that a research agent researches.

> **Eval set:** 12 questions, frozen, checked into `evals/`. Four `standard`, six `deep`, two `exhaustive`. Mix: one with a known contradiction between reputable sources; one where the correct answer is "no reliable source says this"; one requiring a PDF; one requiring a paywalled paper; one requiring a dead link; one time-sensitive (answer changed in the last 6 months); one multi-entity enumeration (the case single agents famously fail).

> **Judge rubric** (end-state, LLM-judged, 0–3 each): factual accuracy · citation validity (every `[S#]` resolves and the span actually supports the claim) · coverage of the decomposition · contradiction handling · calibration (does it say what it did not find) · concision.

> **Deterministic gates** (no judge needed, run in CI against recorded fixtures):

| Gate | Threshold |
| --- | --- |
| Unresolvable `[S#]` markers | 0 |
| Claims with statistics and no marker | 0 |
| `claim_verify` unsupported in the final brief | 0 |
| Duplicate fetches of the same canonical URL | 0 |
| Tokens per registered tier-A/B source | ≤ 8 k, tracked as a trend |
| Wall clock within tier budget | 95th percentile |
| Corpus files with no ledger entry, or vice versa | 0 |

> **Regression harness:** record fixtures (search results, page bodies) so the deterministic gates run offline in CI. The judge runs nightly, not per commit.

### §11 Build order

`docs/HDR-SPEC.md` lines 805–822. Each phase is independently mergeable. Do not start a phase before the previous one's acceptance criteria pass.

Quoted acceptance that official STOPs later change:

- P1: `hermes profile install` succeeds; `/tools list` shows `delegation, browser, vision, code_execution, moa, clarify, todo, hdr`. Also delivers a “repo-root distribution index”.
- P9: With `web_extract` disabled, `web-fallback-fetch` appears and the run still completes.
- P10: 12/12 run to completion; rubric mean ≥ 2.4.
- P11: Every limitation in §13 is stated in the shipped docs.

### §13 Honest limits of v2

`docs/HDR-SPEC.md` lines 835–847. Eight bullets. The spec says: “State these in the shipped README.”

### §1.1 Gap register

`docs/HDR-SPEC.md` lines 30–60. G01–G25. Severity S1 / S2 / S3.

---

## 2. §10 Evaluation — row by row

### 2.1 The 12-question set

**MATCH (minor).** `evals/questions.json` ships exactly 12 frozen questions. Tiers: 4 `standard` (Q01–Q04), 6 `deep` (Q05–Q10), 2 `exhaustive` (Q11–Q12). `tests/test_hdr_eval_gates.py::test_twelve_questions` asserts that mix.

Required kinds are present:

| Spec mix item | Question | Kind |
| --- | --- | --- |
| Known contradiction | Q03 “Do reputable sources agree on whether toolset moa exists” | `contradiction` |
| No reliable source says this | Q04 “Which official Hermes page names an army-runtime toolset?” | `no-source` |
| Requires a PDF | Q06 | `pdf` |
| Requires a paywalled paper | Q07 | `paywall` |
| Requires a dead link | Q08 | `dead-link` |
| Time-sensitive (last 6 months) | Q09 MoA toolset → provider | `time-sensitive` |
| Multi-entity enumeration | Q10 HDR bundle toolsets | `multi-entity` |

**DRIFT (minor).** Q04 is a clean “no source names this” item. The brief it wants is “I did not find.” The fixture pages already contain the answer (“No army-runtime toolset is listed”). That is a negative-finding question with positive fixture text. Fine for offline FakeCtx. Weak as a live “no reliable source” probe.

**DRIFT (minor).** Q06 says “fixture PDF paper.” `evals/fixtures/questions.json` Q06 pages are HTML-shaped strings, not a PDF byte stream. The second page *mentions* `pdf_text.py`. The offline loop never opens a PDF.

**DRIFT (minor).** Q07 paywall page is a short fixture string with `fetch_status: paywall`. No Unpaywall HTTP. No real OA miss.

**DRIFT (minor).** Q11 asks to map every gap G01–G25. The fixture only has two pages (G01 and G05). An exhaustive due-diligence item is stubbed.

**EXTRA (docs).** `evals/questions.json` also names `judge_rubric` and `judge_scale: "0-3 end-state; nightly, not per commit"`. That matches §10’s rubric list.

### 2.2 Offline fixtures ≠ live judge

**MATCH (major, intended).** Two harnesses exist and they are not the same thing.

1. **Recorded fixture runs** (`evals/fixtures/run_a|run_b|run_c/`). Hand-written `brief.md` + `ledger.json` + `audit.json` + `corpus/*.txt`. `evals/gates.py::check_run` scores them. CI calls this via `tests/test_hdr_eval_gates.py::test_three_fixture_runs_pass_gates`.
2. **12-question offline loop** (`evals/run_offline.py`). Loads `evals/questions.json` + `evals/fixtures/questions.json`. Spins a temp `HERMES_HOME`. Loads the hdr plugin through `tests/test_hdr_plugin.py::FakeCtx`. Feeds pages through `transform_tool_result`. Drafts a brief with `store.draft.draft_brief()`. No Hermes CLI. No model. No `web_search` / `web_extract`. No skill index.
3. **Nightly judge** (`evals/nightly_judge.py`). Not in `.github/workflows/validate.yml`. Skips unless `HDR_JUDGE_MODEL` is set. Even then it scores the *offline FakeCtx briefs* with the mechanical rubric. Optional `HDR_JUDGE_CMD` can pipe JSON to a host command. The file itself says: “Do not invent a model id or an HTTP provider.”

**UNPROVEN (blocker for P10 live acceptance).** No file records a live 12/12 on Hermes 0.19.0. No file records an LLM judge mean ≥ 2.4 on live briefs. `evals/smoke/P1-LIVE.md` is install + `tools list` + `skills list` only.

**DRIFT (major).** `evals/rubric.py` is titled “Mechanical end-state rubric. Nightly LLM judge is separate.” The nightly script then *is* that mechanical rubric, plus an optional host command. Spec §10: “Judge rubric (end-state, **LLM-judged**).” Shipped nightly is not an LLM judge unless the operator invents `HDR_JUDGE_CMD`. There is no scheduled workflow named nightly.

**DRIFT (major).** `evals/nightly_judge.py` and `tests/test_hdr_eval_gates.py::test_twelve_questions_complete_offline` both call `score_brief(..., gate_errors=[])`. The 12-question mean ≥ 2.4 does **not** run `check_run`. It scores the drafted brief’s shape (markers, word count, a few regexes). A brief that would fail citation gates can still mean ≥ 2.4.

**DRIFT (minor).** `run_offline.py` always creates the run at `tier: "standard"` even for Q11/Q12 (`exhaustive`) and Q05–Q10 (`deep`). Effort scaling is not exercised by the 12-question loop.

### 2.3 Deterministic gates vs §10 table

File: `evals/gates.py`.

| Spec gate | Shipped? | Verdict |
| --- | --- | --- |
| Unresolvable `[S#]` = 0 | Yes. Regex `\[S(\d+)\]` vs ledger `sources[].id`. | **MATCH** |
| Statistics with no marker = 0 | Yes. Percents, years, comma-grouped numbers. | **MATCH** (heuristic; “12 widgets” without `%` or year can slip) |
| `claim_verify` unsupported in the final brief = 0 | **No.** `_unsupported_claims` does *not* call `claim_verify`. It takes the first six `[A-Za-z0-9%]{4,}` tokens from the cited sentence and asks whether any appear in the corpus text. That is lexical overlap. Spec §3.4 deleted that algorithm. | **DRIFT (major)** |
| Duplicate fetches of the same canonical URL = 0 | Yes, but only against `audit.json` `fetches` as written. Fixtures list raw URLs, not canonicalized URLs. | **MATCH** on fixtures; **UNPROVEN** on live audit shape |
| Tokens per tier-A/B source ≤ 8 k, tracked as a trend | Yes as `tokens / tier_ab_sources > 8000`. Fixtures hand-write `tokens` and `tier_ab_sources`. No trend file. No history. | **PARTIAL / DRIFT (minor)** — threshold exists, trend does not |
| Wall clock within tier budget, 95th percentile | Yes as `wall_seconds > tier_budget_seconds` **per run**. No percentile. Three fixtures cannot make a 95th. | **DRIFT (minor)** |
| Corpus ↔ ledger orphans = 0 | Yes. Extra / missing filenames. Also checks quote-in-corpus. | **MATCH** |

Fixture runs used as the CI gate:

| Run | Kind | What it proves |
| --- | --- | --- |
| `run_a` | contradiction | MoA official vs stale secondary; army-runtime absent. Brief names the disagreement. |
| `run_b` | paywall | Abstract cited; “no OA copy”; `fetch_status: paywall`. |
| `run_c` | dead-link | Wayback snapshot; archived URL stored. |

Those three pass `check_run` today. They are authored artifacts, not agent output.

**GAP (major).** There is no fixture that fails on purpose and is asserted to fail. A broken gate would still be green if the three happy briefs stay happy.

**GAP (minor).** Spec: “record fixtures (search results, page bodies).” `evals/fixtures/questions.json` records page bodies. It does not record `web_search` hit lists. The offline loop injects extracts only.

### 2.4 CI vs live

`.github/workflows/validate.yml`:

- `python scripts/validate_factory.py` — structure only. Comment: “Does not call Hermes or Context7.”
- `python -m unittest discover -s tests -v` — isolated `HERMES_HOME`. Comment: “No live Hermes.”

**MATCH** with the factory rule “CI is structure-only.”

**MATCH** with the task brief: “Structure-only CI has no Hermes CLI.”

**UNPROVEN (blocker for P9/P10 live).** Live P1 is recorded. Live P9 (skill index with `web_extract` disabled) is not. Live P10 (12/12 + LLM judge) is not.

`scripts/hdr_live_smoke.sh` installs a named profile and runs `tools list`, `skills list`, `plugins list`. It does not disable `web_extract`. It does not run the 12 questions. It does not invoke a judge.

`evals/smoke/P1-LIVE.md` records Hermes Agent **v0.19.0** from PyPI on 2026-08-27:

```text
hermes profile install /workspace/agents/research-bot --name research-bot-hdr --yes
✓ Installed 'research-bot-hdr' v2.0.0
```

Enabled toolsets: `web, browser, vision, file, terminal, code_execution, skills, memory, session_search, todo, clarify, delegation, cronjob, hdr`.

No `moa` line. Skills listed: `claim-audit, deep-research-run, literature-sweep, source-triage, web-fallback-fetch`. Doctor is explicitly not a command.

That is P1 live. It is not P9 or P10 live.

### 2.5 Plugin unit tests that touch eval acceptance

`tests/test_hdr_plugin.py` (eval-related only):

| Test | Spec phase it supports |
| --- | --- |
| `test_register_surfaces` | P1 / P5 — tools on toolset `hdr`; no `source_ledger_check`; prompt sections ≤ 4k / 8k |
| `test_migration_idempotent` | P2 |
| `test_eight_thread_writes` | P2 — 8 threads, 8 distinct ids |
| `test_evidence_bus_card_and_byte_exact` | P3 — 40k+ page → card ≤400 tokens; fail-open |
| `test_dedupe_and_citation_gate` | P4 |
| `test_write_allowlist` | P4 |
| `test_plan_digest_and_gap_scan` | P5 — digest ≤1200; `gap_scan` returns a float |
| `test_three_worker_batch_parent_stays_small` | P6 — 3 mandates; parent < 4k tokens; no raw page in harvest |
| `test_claim_verify_and_conflicts` | P7 |
| `test_governor_forced_overspend` | P8 |
| `test_web_fallback_completes_without_web_extract` | P9 **unit** — frontmatter has `fallback_for_tools: [web_extract]`; `evidence_add` still drafts a brief. Does **not** ask Hermes whether the skill appears in the index. |
| `test_amber_named_gap_depth` | P8 / §3.6 AMBER named-gap |

**MATCH** for offline unit acceptance of P2–P8.

**UNPROVEN** for P6 live fan-out (real `delegate_task` children).

**UNPROVEN** for P9 live skill index.

### 2.6 Factory validator vs eval leftovers

`scripts/validate_factory.py` does the right bans for *cross-profile* names: `army`, `army-runtime`. It requires research-bot skills to be the five HDR names. It requires `claim-audit` to say `source_ledger_check` is gone. It forbids `moa` in `custom_toolsets.research`. It requires `plugins.enabled: [hdr]`.

It does **not** read `docs/PROFILE-PLAYBOOK.md` for leftover v1 tool names. `check_playbook()` only asserts isolation phrases and official URLs. A playbook that still says `plugins/research-bot/` and `source_ledger_check` still passes CI.

**GAP (blocker for the factory).** The playbook is the source of truth for the next profile. CI will not fail when it teaches v1.

---

## 3. §11 Build order — P0 through P11

Each row: spec deliverable / acceptance, then whether `main` implements it, partially implements it, or only documents it.

### P0 — Doc probe

**Deliverable:** `docs/HERMES-FACTS.md` for every `[DOC]` and `[UNV]`.

**Acceptance:** Every `[UNV]` in the spec is `[DOC]` or removed.

**Status: implemented** (the facts file). The spec file itself was **not** rewritten.

`docs/HERMES-FACTS.md` probe date 2026-08-27. Context7 `/nousresearch/hermes-agent`. Official STOP on `moa`. `[UNV]` register: CDP env, invented academic MCP, `>=0.14.0`, `pre_tool_call` vs `delegate_task`, child `HERMES_HOME`, `ctx.llm`, Camofox — all `[DOC]` or **Removed**.

**DRIFT (docs, major for anyone who reads the spec as install instructions).** `docs/HDR-SPEC.md` still contains the unresolved text:

- §4.2 bundle still lists `- moa` (line 355).
- §4.2 `mcp_allowlist: [context7, openalex, pubmed, wayback]` (line 368).
- §4.3 table still lists `openalex` / `pubmed` / `wayback` as `[UNV]` servers (lines 393–395).
- §4.7 still shows `hermes_requires: ">=0.14.0"` (line 460) and `hermes plugins doctor <profile>/plugins/hdr --ci` (line 483) and “Add a repo-root `distribution.yaml`” (line 481).
- §11 P1 acceptance still requires `/tools list` to show `moa` and a repo-root index (line 812).

Shipped `agents/research-bot/config.yaml` and `distribution.yaml` follow the facts file, not those leftover spec lines. A later agent who implements the spec literally will re-introduce four official STOPs.

**Verdict: MATCH** on P0 *deliverable*. **DRIFT** on P0 *acceptance* if “every `[UNV]` in this spec” means the spec text itself is cleaned.

### P1 — Config + surfaces

**Deliverable:** `config.yaml` v2, toolset bundle, `distribution.yaml` v2, repo-root distribution index.

**Acceptance (spec):** install succeeds; `/tools list` shows delegation, browser, vision, code_execution, **moa**, clarify, todo, hdr.

**Official STOPs applied on main:**

1. No `moa` in the bundle. `evals/smoke/P1-LIVE.md` confirms no `moa` line.
2. No repo-root `distribution.yaml`. Root README and `HERMES-FACTS.md` §16 say path install only.
3. No `plugins doctor`. Profile README tells the operator to use `plugins list` / `tools list`.
4. `hermes_requires: ">=0.13.0"` in `agents/research-bot/distribution.yaml`. Comment: 0.14.0 was `[UNV]` and removed.

**Status: implemented**, with the four STOPs. Live recorded.

**DRIFT (docs):** spec §11 P1 acceptance text still names `moa` and a repo-root index. Factory docs that still say `plugins.enabled: [<name>]` with `<name>` = profile name will make the next profile enable a plugin named `research-bot`, not `hdr`.

Shipped bundle (`agents/research-bot/config.yaml` `custom_toolsets.research`): `web, browser, vision, file, terminal, code_execution, skills, memory, session_search, todo, clarify, delegation, cronjob, hdr`. Matches P1-LIVE.

`x_search` is in G24’s “missing surfaces” list. `HERMES-FACTS.md` §10: “Not in the HDR bundle.” Runtime still treats `x_search` as a network tool if the host enables it (`runtime.py` `NETWORK_TOOLS`). That is defence, not a shipped toolset.

### P2 — Store layer

**Deliverable:** `store/` + schema v2 + v1 migration, no hooks yet, unit-tested.

**Acceptance:** migration idempotent; 8-thread writes lose nothing.

**Status: implemented.** `agents/research-bot/plugins/hdr/store/` exists (`bus`, `ledger`, `claims`, `run`, `extract`, `score`, `spans`, `sanitize`, `index`, `draft`). `LEDGER_VERSION = 2`. `migrate_v1` in `ledger.py`. Tests: `test_migration_idempotent`, `test_eight_thread_writes`.

The phase text said “no hooks yet.” Main already has hooks (later phases). That is expected on a merged tree. Not a gap.

### P3 — Evidence Bus

**Deliverable:** `transform_tool_result` intake, canonicalization, extraction, tiering, spans.

**Acceptance:** 40k-char page → card ≤400 tokens; corpus byte-exact; hook fails open.

**Status: implemented.** `hooks/intake.py` + `test_evidence_bus_card_and_byte_exact`.

### P4 — Policy engine

**Deliverable:** `pre_tool_call`: dedupe fence, write allowlist, Citation Gate.

**Acceptance:** second fetch blocked with a card reference; brief with unresolvable `[S#]` refused with the offending sentence.

**Status: implemented** in unit tests (`test_dedupe_and_citation_gate`, `test_write_allowlist`). Live Citation Gate **UNPROVEN**.

### P5 — Plan + loop tools

**Deliverable:** `research_plan`, `gap_scan`, `evidence_*`, prompt sections, volatile digest.

**Acceptance:** digest ≤1 200 chars; sections within 4k/8k; `gap_scan` returns a real saturation number.

**Status: implemented** offline (`test_plan_digest_and_gap_scan`, `test_register_surfaces`). Live loop **UNPROVEN**.

### P6 — Fan-out

**Deliverable:** `worker_brief`, `worker_harvest`, subagent hooks, `delegation.*` config.

**Acceptance:** 3 parallel workers on disjoint mandates; parent context grows < 4k tokens; zero raw page text in the parent.

**Status: partially implemented.** Unit test simulates three briefs + harvest from written transcript files. It does not call Hermes `delegate_task`. Config has `max_concurrent_children: 5`, `max_spawn_depth: 2`. Live 3-child batch **UNPROVEN**.

### P7 — Verification

**Deliverable:** `claim_verify`, `conflict_report`, `cite_source` v2, `transform_llm_output`.

**Acceptance:** every deterministic gate in §10 passes on 3 fixture runs.

**Status: implemented** for the three *authored* fixture runs. Plugin `claim_verify` is exact-span (`store/spans.py::verify_claim`). CI gate `_unsupported_claims` is **not** that function — see §2.3. So P7’s *tool* MATCHES. P7’s *eval gate* DRIFTS.

### P8 — Governor

**Deliverable:** `pre/post_api_request` accounting, AMBER/RED/HARD fences.

**Acceptance:** a forced-overspend fixture stops fetching and produces a brief from what it has.

**Status: implemented** offline (`test_governor_forced_overspend`, `test_amber_named_gap_depth`). Live overspend **UNPROVEN**.

### P9 — Skills + scripts

**Deliverable:** five skills, `scripts/`, correct frontmatter, `fallback_for_tools`.

**Acceptance:** with `web_extract` disabled, `web-fallback-fetch` appears and the run still completes.

**Status: partially implemented.** Five skills exist. Frontmatter is nested `metadata.hermes`. `web-fallback-fetch` has `fallback_for_tools: [web_extract]`. P1-LIVE lists the skill as enabled **with** `web` present — so the fallback should be *hidden* on that host, and the note does not say it was hidden. Unit test completes a run by calling `evidence_add` directly. It never asks Hermes to hide/show the skill.

**UNPROVEN (blocker for P9 acceptance).** No `evals/smoke/P9-LIVE.md`. No recording that `hermes -p … skills list` dropped or showed `web-fallback-fetch` after disabling `web_extract`.

### P10 — Eval

**Deliverable:** `evals/`, fixtures, CI gates, nightly judge.

**Acceptance:** 12/12 run to completion; rubric mean ≥ 2.4.

**Status: partially implemented.**

| Claim | What main has |
| --- | --- |
| 12/12 complete | Offline FakeCtx + `draft_brief` completes 12/12. **UNPROVEN** live. |
| Rubric mean ≥ 2.4 | Mechanical rubric on those drafts, with `gate_errors=[]`. Three authored fixtures also mean ≥ 2.4. **UNPROVEN** LLM-judged. |
| Nightly judge | Script exists. No cron. No workflow. Skips without `HDR_JUDGE_MODEL`. |
| CI gates | Three authored runs + question-shape + offline 12/12. |

### P11 — Docs

**Deliverable:** rewritten deep-dive, README, `HONEST-LIMITS.md`.

**Acceptance:** every §13 limitation is stated in the shipped docs.

**Status: partially implemented.** Deep-dive, profile README, and `HONEST-LIMITS.md` are v2. Root README table cell and the factory playbook are still v1. See §5 and §6.

---

## 4. §13 Honest limits — spec vs shipped

Spec §13 (eight bullets) vs `docs/HONEST-LIMITS.md` vs `agents/research-bot/README.md` “Honest limits” vs root `README.md`.

| # | Spec §13 | `HONEST-LIMITS.md` | Profile README | Root README |
| --- | --- | --- | --- | --- |
| 1 | `pre_verify` does not fire for markdown-only turns. Citation Gate is `pre_tool_call` on the brief write. Mitigation: `transform_llm_output`. | Same, plus “A user who reads the answer in chat without a file write bypasses it.” | Same | **GAP** — not stated |
| 2 | `claim_verify` proves a span exists. It does not prove the document is right. Failure mode moves from fabrication to misreading. | Same | Same | **GAP** |
| 3 | Source tiering is a heuristic. | Same | Same | **GAP** |
| 4 | Evidence Bus can only distil what the extractor returned. Canvas/images → `vision_analyze`, lossy. | Same | Same | **GAP** |
| 5 | Prompt-injection is defence in depth. Docker is the boundary. | Same | Same | **GAP** |
| 6 | Children writing to a shared ledger is `[INF]` until P0 verifies `HERMES_HOME`. Transcript-grep backstop exists because of that uncertainty. | **DRIFT (docs, intended):** “P0 resolved profile-home `plugin-data/` and live transcripts as `[DOC]`. The transcript-grep backstop stays.” | Same as HONEST-LIMITS | **GAP** |
| 7 | Budget numbers are starting points. P10 replaces them with measurements. | “P10 fixtures track tokens per tier-A/B source. They are not yet field measurements.” Honest. Matches UNPROVEN P10. | Same | **GAP** |
| 8 | Cross-model MoA is only as good as the second model’s independence. Same-family agreement is weak. | Same, plus official “provider, not a toolset.” | Same | **GAP** |

**EXTRA (docs, good).** HONEST-LIMITS and the profile README add the GitHub-URL / path-install limit. Spec §13 does not have that bullet. Spec §4.7 / G21 do.

**DRIFT (docs).** Spec §13: “State these in the shipped README.” The *profile* README does. The *root* README does not. Root README is the first file a clone reader opens.

**DRIFT (docs).** Spec bullet 6 is still written as `[INF]`. P0 closed it. The spec was not patched. HONEST-LIMITS was.

**MATCH.** Deep-dive §11 points at HONEST-LIMITS. Profile README copies the list. `docs/INTEGRATION.md` states the `pre_verify` markdown-only fact in the hooks section.

---

## 5. §1.1 Gap register — closed in code vs only in docs

“Closed in code” means a plugin, config, skill, or test implements the fix. “Docs only” means a file *says* it is fixed and the mechanism is missing or unproven.

| # | Gap (spec) | Code on main | Docs | Verdict |
| --- | --- | --- | --- | --- |
| G01 | No research loop | `research_plan`, `gap_scan`, `run.json`, `deep-research-run` | Deep-dive §5 | **Closed in code.** Live loop UNPROVEN. |
| G02 | No fan-out / `delegation` missing | `delegation` in bundle; `worker_brief` / `worker_harvest` | Deep-dive §8 | **Closed in code.** Live 3-child UNPROVEN. |
| G03 | Zero context-economics | `config.yaml` compression, tool_output, tool_budget, file_read_max_chars, prompt_caching, `run_budget_seconds` | Deep-dive §4 | **Closed in code.** |
| G04 | Page text thrown away | Evidence Bus corpus + cards | Deep-dive §6 | **Closed in code.** |
| G05 | `source_ledger_check` lexical overlap | Plugin `claim_verify` is exact-span. **CI `_unsupported_claims` is still overlap.** Playbook still names `source_ledger_check` as a ledger tool. | HERMES-FACTS / claim-audit skill say it is gone | **Closed in plugin. Open in eval gate + playbook. DRIFT (major).** |
| G06 | Static contract re-injected every turn | `register_system_prompt_section` (`hdr.method`, `hdr.effort`, `hdr.integrity`); digest on `pre_llm_call` ≤1200 | INTEGRATION | **Closed in code.** |
| G07 | No token circuit breaker | Governor GREEN/AMBER/RED/HARD | Deep-dive §7 | **Closed in code.** Live UNPROVEN. |
| G08 | Single-path web, keyless off | Bundle has browser/vision; `keyless_fallback: true`; `archive_lookup`; literature scripts | Profile README env table | **Closed in code.** Playbook still teaches `keyless_fallback: false`. **DRIFT (blocker for next profile).** |
| G09 | Context7 as research spine / no URL | Facades require an openable `https://` URL (`test_docs_query_requires_openable_url`) | INTEGRATION | **Closed in code.** |
| G10 | Thin ledger schema | v2 fields: dates, authors, DOI, canonical URL, stance, tier, claims | — | **Closed in code.** |
| G11 | Malformed citations | `cite_source` uses authors/date/publisher; Crossref HTTP helper | — | **Closed in code.** Quality UNPROVEN live. |
| G12 | No injection handling + local terminal | `terminal.backend: docker`; `sanitize.wrap`; untrusted wrapper setting | HONEST-LIMITS | **Closed in config + sanitizer.** Limit honestly stated. |
| G13 | Porous write fence | Allowlist dirs; terminal effect fence | Deep-dive §7 | **Closed in code** relative to v1. Not a proof against every heredoc. |
| G14 | No subagent story | Child brief contract, harvest, `subagent_*` hooks, cheap-child comment | INTEGRATION | **Closed in code.** Live UNPROVEN. |
| G15 | No verification / triangulation | `claim_verify`, `conflict_report`, `transform_llm_output` | Deep-dive §5 | **Closed in code.** |
| G16 | Skill frontmatter shape wrong | All five skills use `metadata.hermes` | Playbook still shows *flat* `requires_toolsets:` in the copy-paste block (lines 323–330) | **Closed in shipped skills. Open in playbook. DRIFT (blocker).** |
| G17 | No skill `scripts/` | Each HDR skill that needs a parser has `scripts/` | Playbook still says helper scripts “only when parsing cannot live in the plugin” and lists v1 skill names | **Closed in code.** Playbook example set is v1. |
| G18 | Three overlapping skills | Five disjoint skills | Playbook still lists `literature-review`, `claim-check` | **Closed in code. Playbook DRIFT (blocker).** |
| G19 | Honcho unbounded recall | `memory_char_limit: 1600`, `user_char_limit: 900`; INTEGRATION one-paragraph Honcho | Playbook still has a long Honcho section (method, not HDR-specific) | **Closed enough in config.** |
| G20 | No observability / eval | `evals/` + CI gates + nightly *script* | Deep-dive §10 | **Partial.** Structure MATCH. Live 12/12 + LLM judge UNPROVEN. |
| G21 | No repo-root `distribution.yaml` | **Intentionally not added.** Official STOP: do not invent a multi-profile index. Path install documented. | Root README, HERMES-FACTS §16, P1-LIVE | **Closed by official STOP, not by implementing the spec line.** Spec §4.7 / §11 still ask for the index. **DRIFT in spec vs facts.** |
| G22 | Stale compression / child session | `compression.in_place: true` in config; FACTS §5 | Playbook still says “Do not code a dependency on `in_place`” and repeats the child-session overlap flag | **Closed in HDR config. Playbook still UNVERIFIED on a [DOC] fact. DRIFT (major for next profile).** |
| G23 | Leaf `execute_code` UNVERIFIED | FACTS: both roles keep `execute_code`. INTEGRATION repeats that. Playbook still says leaf cannot call `execute_code` and marks it UNVERIFIED. | Playbook lines 449–453 | **Closed in HDR docs. Playbook DRIFT (major).** |
| G24 | Missing surfaces | Bundle has browser, vision, code_execution, todo, clarify, cronjob, hdr. **No `moa` toolset (STOP). No `x_search` (FACTS: not in bundle).** | FACTS §10 | **Closed for the shipped bundle.** Spec G24 still lists `moa` as a missing capability to add. |
| G25 | No effort scaling | Tiers in `research_plan`; `hdr.effort` section; AMBER named-gap test | Deep-dive | **Closed in code.** Offline loop ignores tier. |

---

## 6. Factory / user-facing leftover catalog

Grep targets: `army`, `army-runtime`, `source_ledger_check`, `source_ledger_add`, `source_ledger_list`, `toolset research-bot`, `plugin research-bot`, `moa` toolset, `plugins doctor`, invented `0.14.0`.

Plus every v1 name the playbook still teaches (`literature-review`, `claim-check`, `keyless_fallback: false`, `plugins/<name>/` as if plugin id must equal profile name).

### 6.1 `docs/PROFILE-PLAYBOOK.md` — KNOWN STALE — full leftover list

This file is the source of truth for every later profile. Leftovers here are **blocker** even when HDR code is correct.

| Loc | Leftover | What is true on main | Class / sev |
| --- | --- | --- | --- |
| L43 | “Live process code lives only in `agents/<name>/plugins/<name>/`.” | research-bot ships `agents/research-bot/plugins/hdr/`. Plugin id ≠ profile name. | **DRIFT / blocker** |
| L44 | “`research-bot` is the toolset id for that profile only. Do not enable it on any other profile. Do not rename it.” | Toolset id is `hdr`. Spec §4.4 / §5.1 renamed it on purpose. | **DRIFT / blocker** |
| L123 | “The research-bot plugin registers `resolve_library` and `docs_query`.” | The **hdr** plugin registers those tools. | **DRIFT / docs** |
| L138–147 | Gather block with `keyless_fallback: false` and `keyless_rescue: false`. “research-bot already does.” | `agents/research-bot/config.yaml` sets both **true**. Validator *requires* true. | **DRIFT / blocker** |
| L160–164 | “Turn the keyless ring off.” | HDR v2 turns it on so a dead primary path degrades. | **DRIFT / blocker** |
| L179 | Skills `literature-review`, `source-triage`, `claim-check`. | Shipped: `deep-research-run`, `source-triage`, `claim-audit`, `literature-sweep`, `web-fallback-fetch`. | **DRIFT / blocker** |
| L195 | “Plugin (research-bot) \| Facade + ledger + user-message contract.” | Plugin name `hdr`. Hooks include Evidence Bus, governor, bibliography — not only those three. | **DRIFT / major** |
| L261–274 | Scaffold `agents/<name>/plugins/<name>/` and `plugin.yaml` `name: <name>`. | Legal for a *new* profile that chooses matching ids. Fatal as a description of research-bot. Next author will copy `plugins/research-bot`. | **DRIFT / blocker** |
| L289 | “typically the profile name (`research-bot`). The plugin registers each tool with `toolset="<name>"`.” | research-bot’s toolset is `hdr`. | **DRIFT / blocker** |
| L293 | “It does not enable `research-bot`.” | Should say it does not enable `hdr` either, unless it independently needs HDR. | **DRIFT / major** |
| L323–330 | Flat YAML `requires_toolsets:` / `requires_tools:` (G16 shape). | Shipped skills nest under `metadata.hermes`. FACTS §14: v1 flat keys are the wrong shape. | **DRIFT / blocker** |
| L332 | `requires_toolsets: [research-bot]` example. | Should be `[hdr]` if the example is this profile. | **DRIFT / blocker** |
| L334 | “`research-bot` skills require `resolve_library`, `docs_query`, and `cite_source`.” | Only part of the v2 set. `deep-research-run` requires `research_plan`, `gap_scan`, `cite_source`, `delegate_task`. | **DRIFT / major** |
| L409 | Compression “generate a new session lineage id (child session).” | G22 / FACTS: `in_place: true` is the documented default. | **DRIFT / major** |
| L415 | “Do not code a dependency on `in_place`.” | HDR *does* set `in_place: true`. Durable store is still `plugin-data/`, which is correct either way. | **DRIFT / minor** |
| L449–453 | Leaf cannot call `execute_code`. UNVERIFIED. | FACTS G23 resolved: both roles keep `execute_code`. INTEGRATION agrees. | **DRIFT / major** |
| L521 | Plugin path `agents/research-bot/plugins/research-bot/` | Path is `agents/research-bot/plugins/hdr/` | **DRIFT / blocker** |
| L522 | `plugins.enabled` `[research-bot]` | `[hdr]` | **DRIFT / blocker** |
| L523 | Toolset `research-bot` | `hdr` | **DRIFT / blocker** |
| L525 | Skills `literature-review`, `source-triage`, `claim-check` | Five v2 skills | **DRIFT / blocker** |
| L526 | Skill gate `requires_toolsets: [research-bot]` + `resolve_library, docs_query, cite_source` | `metadata.hermes.requires_toolsets: [hdr, …]` | **DRIFT / blocker** |
| L527 | Bundle includes `web` and `research-bot` | Bundle includes the full HDR list + `hdr` | **DRIFT / blocker** |
| L529 | Ledger tools `source_ledger_add`, `source_ledger_list`, `cite_source`, `source_ledger_check` | `evidence_*`, `claim_verify`, `cite_source`. Spec §5.3: check is **deleted, not renamed**. | **DRIFT / blocker** |
| L531 | Hook list: `on_session_start`, `pre_llm_call`, `pre_tool_call`, `post_tool_call` only. “does not police `delegate_task`.” | hdr also registers Evidence Bus, governor, `subagent_*`, `transform_llm_output`. Governor **does** block `delegate_task` on AMBER/RED/HARD. | **DRIFT / major** |

Playbook items that are still **MATCH** (keep them when rewriting):

- Isolated `HERMES_HOME`. No shared plugin / toolset / runtime. No army.
- Path install. No repo-root `distribution.yaml`.
- Four surfaces never collapsed.
- SOUL is identity. No tools in SOUL.
- Honcho is `memory.provider`, not `plugins.enabled`.
- `distribution_owned` must list `plugins`.
- Facade tools + `ctx.call_mcp`. No `tools.include: []`.
- Gather builtins `web_search` / `web_extract`. Do not register a search tool.
- One agent per PR. Zero imports from another profile’s plugin.

### 6.2 Root `README.md`

| Loc | Leftover | Class / sev |
| --- | --- | --- |
| L47 table cell | “Ships **its own** `research-bot` plugin and toolset.” | **DRIFT / blocker.** Shipped plugin/toolset is `hdr`. This is the known stale cell. |
| Whole file | Does not state §13 limits. Spec P11 / §13 ask for the shipped README. | **GAP / docs** |
| L55 | `plugins.enabled: [<name>]` and `requires_toolsets` of “this profile’s toolset” | **MATCH** as generic advice. Dangerous next to L47, which implies `<name>` = `research-bot`. |

Product framing (library, path install, no root index) is **MATCH**.

### 6.3 `AGENTS.md`

| Loc | Leftover | Class / sev |
| --- | --- | --- |
| L23 | “Live process code lives only in `agents/<name>/plugins/<name>/`. Toolset `research-bot` stays on that profile only.” | **DRIFT / major.** Path template and toolset name are v1. |

Isolation rules otherwise **MATCH**.

### 6.4 `docs/WORKFLOW.md`

| Loc | Leftover | Class / sev |
| --- | --- | --- |
| L29 | `plugins/<name>/` and `plugins.enabled: [<name>]` | **DRIFT / major** if read as “name the plugin after the profile.” |
| L31 | “Toolset `research-bot` stays on that profile only.” | **DRIFT / major.** Toolset is `hdr`. |
| L35–38 | Presents `hermes plugins doctor [path-or-id] --ci` as official. | **DRIFT / blocker.** Official STOP: not a command on 0.19.0. FACTS quotes the CLI error. |
| L44 | Smoke: `Use the literature-review skill` | **DRIFT / major.** That skill name does not exist. |

### 6.5 `docs/INTEGRATION.md` (factory)

**MATCH.** Line 11: “research-bot ships plugin `hdr` (toolset `hdr`). The next profile writes its own plugin, toolset, and skills. Zero imports from `hdr`.”

This is the factory file that was updated. The playbook and WORKFLOW were not.

### 6.6 `docs/research-bot-deep-dive.md`

**MATCH** for naming, loop, eval, install, `>=0.13.0`, no `moa`.

**GAP (docs, minor).** §10 Eval describes CI gates and nightly judge as if P10 acceptance is done. It does not say live 12/12 and the LLM judge are unproven. Profile README *does* say that (line 110). Deep-dive is less honest than the profile README.

### 6.7 `docs/HONEST-LIMITS.md` / `docs/HERMES-FACTS.md`

**MATCH** for this slice. FACTS is the STOP register. HONEST-LIMITS is the P11 list, with the P0 `[DOC]` update on child ledger paths.

`army` does not appear in either file as a product name. Good.

### 6.8 `agents/research-bot/README.md` and `INTEGRATION.md`

**MATCH.** Plugin `hdr`. Toolset `hdr`. No doctor. No `moa` toolset. `source_ledger_check` mentioned only as gone. §13 limits copied. Live P1 pointer. Offline vs live honesty on line 110.

### 6.9 `.cursor/rules/hermes-factory.mdc`

| Loc | Leftover | Class / sev |
| --- | --- | --- |
| L30 | “keyless ring off.” | **DRIFT / major.** HDR v2 and `validate_factory.py` require keyless **on** for research-bot. The Cursor rule will fight the validator and the playbook’s stale block will agree with the rule. Two wrong files, one right config. |

The rule still points at the playbook as SoT. That multiplies the playbook leftovers.

### 6.10 `scripts/validate_factory.py` leftover messages (not user-facing, but it teaches CI authors)

| Loc | Text | Class |
| --- | --- | --- |
| L171 | Error path `agents/<name>/plugins/<name>/` | **DRIFT / docs** — research-bot would be illegal under that sentence, yet it ships `plugins/hdr/` and the validator allows it. |
| L507–513 | Other profiles “must not enable the research-bot plugin / toolset research-bot” | **EXTRA / leftover.** Correct ban of a v1 id. Does not ban copying `hdr`. Does not fail the playbook for still teaching those ids. |
| L734–738 | claim-audit must mention `source_ledger_check` is gone | **MATCH** as a tombstone check. |

### 6.11 Grep matrix (factory + evals)

| Needle | Factory / user docs | HDR code / evals | Verdict |
| --- | --- | --- | --- |
| `army` / `army-runtime` | Banned by `validate_factory.py` `_BANNED_DOC_PATTERNS`. No hit in playbook, README, AGENTS, WORKFLOW, INTEGRATION. | Q04 + fixtures + `run_a` brief as a *negative* example (“no army-runtime toolset”). `evals/rubric.py` calibration regex includes `no army`. | **MATCH.** Negative use in evals is fine. |
| `source_ledger_check` | Playbook L529. claim-audit skill (tombstone). | Spec history. Fixture Q11 text. `test_register_surfaces` asserts the name is **absent** from registered tools. | **DRIFT in playbook.** MATCH in plugin. |
| `source_ledger_add` / `source_ledger_list` | Playbook L529 only (factory). | Spec §5.3 rename table. | **DRIFT in playbook.** |
| `toolset research-bot` / `requires_toolsets: [research-bot]` | Playbook L44, L289, L332, L526. AGENTS L23. WORKFLOW L31. | Skills use `[hdr]`. Config bundle lists `hdr`. | **DRIFT (blocker).** |
| `plugin research-bot` / `plugins/research-bot` | Playbook L123, L195, L521–522, L531. README L47. | Shipped dir is `plugins/hdr/`. Validator requires `plugins.enabled == [hdr]`. | **DRIFT (blocker).** |
| `moa` toolset as required | Spec §4.2 and §11 P1. | FACTS STOP. Config comment. P1-LIVE. Skills say there is no `moa` toolset. | **DRIFT in spec. MATCH in shipped profile.** |
| `plugins doctor` | Spec §4.7. **WORKFLOW L35–38 teaches it as official.** | FACTS STOP. Profile README. P1-LIVE. | **DRIFT (blocker) in WORKFLOW.** |
| invented `0.14.0` | Spec §4.7 still shows it. | FACTS removed. `distribution.yaml` is `>=0.13.0`. Deep-dive states the removal. | **DRIFT in spec. MATCH in ship.** |

No factory doc names a toolset or plugin `army`. Good.

---

## 7. Official STOPs — did main keep them?

| STOP | Main | Class |
| --- | --- | --- |
| 1. No `moa` toolset | Config, validator, P1-LIVE, profile README | **MATCH** |
| 2. Path install only | No root `distribution.yaml`. README + FACTS + profile README | **MATCH** |
| 3. No `plugins doctor` on 0.19.0 | Profile README + P1-LIVE + FACTS. **WORKFLOW still teaches it.** | **DRIFT (blocker) in WORKFLOW** |
| 4. No invented academic MCP | `mcp.json` is Context7 only. Facades use HTTP. Spec §4.3 still lists the servers. | **MATCH in ship. DRIFT in spec.** |

Design rule “do not invent Hermes knobs”: FACTS is the probe. Playbook still carries UNVERIFIED `execute_code` / `in_place` / MCP sanitize rows that FACTS already resolved. Next profile will re-litigate closed facts.

---

## 8. ISO 24495-1 notes (user-facing copy only)

These are docs findings, not runtime bugs.

1. Root README table cell fails “point first.” The first profile table a user reads names the wrong plugin.
2. PLAYBOOK §7 table is the one table a later author will copy. It is a v1 dump. One idea per cell is violated: plugin path, enabled id, toolset, skills, gates, and ledger verbs are all wrong at once.
3. WORKFLOW presents `plugins doctor` as a local step before “Official:”. The official 0.19.0 CLI does not have that action. That is a false procedure.
4. Deep-dive §10 states eval as shipped fact. Profile README states the live hole. Two files, two levels of honesty.
5. Keep the words skill, tool, plugin, MCP, SOUL, profile. Factory INTEGRATION already defines them. Playbook defines them, then collapses “the research-bot plugin” with the profile name.

---

## 9. What is already good (do not “fix” these)

1. Plugin package is `hdr`. Tools register on toolset `hdr`. Profile name stays `research-bot`.
2. `docs/INTEGRATION.md`, `docs/research-bot-deep-dive.md`, `docs/HONEST-LIMITS.md`, `docs/HERMES-FACTS.md`, and `agents/research-bot/{README,INTEGRATION}.md` already speak v2.
3. CI has no Hermes CLI and does not claim to.
4. P1 live install on 0.19.0 is written down.
5. Offline 12-question loop and three fixture runs exist and currently pass unit tests.
6. Army names are banned in factory docs and do not appear there.
7. `claim-audit` already says `source_ledger_check` is gone.
8. Validator already requires keyless true, bundle without `moa`, and `plugins.enabled: [hdr]` for research-bot.

---

## 10. Numbered fix list

Herbert: apply these. This review does not apply them.

### Blocker — factory SoT still teaches v1

1. Rewrite `docs/PROFILE-PLAYBOOK.md` so the research-bot *example* uses plugin/toolset `hdr`, path `agents/research-bot/plugins/hdr/`, `plugins.enabled: [hdr]`, five v2 skills, nested `metadata.hermes`, and ledger verbs `evidence_*` / `claim_verify`. Keep the method: the *next* profile invents its own ids. Do not tell anyone to name a toolset `research-bot`.
2. Replace playbook gather block `keyless_fallback: false` / “ring off” with the HDR v2 truth (`true` / degrade, not die), or split “generic gather” from “research-bot v2 gather” so the next web profile is not forced to copy the wrong boolean.
3. Delete playbook §7 rows that name `source_ledger_add`, `source_ledger_list`, `source_ledger_check`, `literature-review`, `claim-check`.
4. Fix playbook skill YAML to `metadata.hermes.requires_toolsets` (G16). Flat keys are how gating silently never applies.
5. Fix playbook `execute_code` / `in_place` to match `docs/HERMES-FACTS.md` (G22, G23). Stop marking resolved facts UNVERIFIED.
6. Fix playbook hook paragraph: governor **can** block `delegate_task`. Do not copy the v1 “does not police `delegate_task`” line as the HDR example.
7. Root `README.md` table cell: “Ships its own **hdr** plugin and toolset.” Keep profile name `research-bot`.
8. `AGENTS.md` L23: `plugins/<id>/` (id may differ from profile name). Toolset `hdr` stays on research-bot. Next profile does not enable `hdr` unless it independently needs it.
9. `docs/WORKFLOW.md`: remove `hermes plugins doctor`. Point at `hermes -p <name> plugins list` and `tools list`. Replace `literature-review` smoke with a skill that exists (`deep-research-run` or a generic `<skill>`).
10. `.cursor/rules/hermes-factory.mdc`: stop saying “keyless ring off” as a library-wide lock, or scope it so it does not contradict research-bot v2.

### Blocker — eval claims vs live proof

11. Do not treat offline FakeCtx 12/12 as P10 acceptance. Add an explicit UNPROVEN note to `docs/research-bot-deep-dive.md` §10 (profile README already has it). Or record live P10 when someone runs it.
12. Record live P9: disable `web_extract`, list skills, show `web-fallback-fetch`, complete one fetch. `evals/smoke/P1-LIVE.md` is not that record.
13. Stop scoring the 12-question loop with `gate_errors=[]` if the mean ≥ 2.4 is meant to be a §10 number. Either run `check_run` on a materialized run dir, or do not claim the gates.

### Major — eval integrity

14. Replace `evals/gates.py::_unsupported_claims` lexical overlap with a call to the same `claim_verify` / `verify_claim` path the plugin uses. The current gate re-implements G05.
15. Either schedule `evals/nightly_judge.py` or stop calling it a nightly LLM judge. Spec: LLM-judged, nightly, not per commit. Shipped: mechanical, on-demand, skipped by default.
16. Wall-clock gate: do not claim 95th percentile. Three fixtures are not a percentile. Rename the gate or collect a series.
17. “Tokens per A/B source, tracked as a trend”: ship a tiny history file or drop “trend” from the docs.
18. Add at least one *failing* fixture (unresolvable `[S#]`, duplicate fetch, orphan corpus) so the gate can go red.

### Major — spec text still contradicts STOPs

19. Patch `docs/HDR-SPEC.md` leftover install instructions, or stamp them “superseded by HERMES-FACTS.” Remaining landmines: §4.2 `moa`, §4.2/`§4.3` invented MCP, §4.7 `>=0.14.0`, §4.7 `plugins doctor`, §4.7 / §11 repo-root index, §11 P1 `/tools list` includes `moa`, §13 bullet 6 still `[INF]`.
20. Validator error strings that say `agents/<name>/plugins/<name>/` should say `agents/<name>/plugins/<plugin-id>/`.

### Minor / docs

21. Root README: add a short pointer to `docs/HONEST-LIMITS.md` so P11’s “shipped README” is true for the first file users open.
22. Q06 fixture: either include a real PDF byte fixture or rename the question so it does not claim a PDF extract.
23. Q11 fixture: either cover G01–G25 or downgrade the question off `exhaustive`.
24. `run_offline.py`: honor each question’s `tier` if effort scaling is part of the eval claim.
25. Factory INTEGRATION is already correct. Do not “align” it back toward the playbook until the playbook is v2.
26. `validate_factory.py::check_playbook` should fail if the playbook still names `source_ledger_*` or `plugins/research-bot/` as current. Today CI cannot see this slice’s blocker.

### Extra (do not invent)

27. Do not add a repo-root `distribution.yaml`.
28. Do not add `moa` to the bundle.
29. Do not add OpenAlex/PubMed/Wayback as Hermes MCP servers.
30. Do not name a toolset or plugin `army` or `army-runtime`.
31. Do not restore `source_ledger_check`.

---

## 11. Summary table

| Area | Verdict | Sev |
| --- | --- | --- |
| §10 question file (12 / 4+6+2 / mix kinds) | **MATCH** | — |
| §10 offline fixtures vs live judge | **MATCH** as a split; live judge **UNPROVEN** | blocker (P10 claim) |
| §10 CI gates on 3 authored runs | **MATCH** (happy path only) | major (no red fixtures; overlap “verify”) |
| §10 nightly LLM judge | **DRIFT** — script is mechanical / optional | major |
| P0 facts file | **MATCH** | — |
| P0 spec text cleaned | **GAP / DRIFT** | major |
| P1 config + live install | **MATCH** with STOPs | — |
| P2–P5, P7 tool, P8 | **Implemented** offline | — |
| P6 live fan-out | **UNPROVEN** | major |
| P9 live skill index | **UNPROVEN** | blocker (acceptance text) |
| P10 live 12/12 + LLM judge | **UNPROVEN** | blocker (acceptance text) |
| P11 HONEST-LIMITS + profile README | **MATCH** | — |
| P11 playbook / root README / WORKFLOW / AGENTS | **DRIFT** v1 leftovers | **blocker** |
| G05 in plugin | **MATCH** | — |
| G05 in CI gate + playbook | **DRIFT** | major / blocker |
| G16/G18/G22/G23 in playbook | **DRIFT** | blocker / major |
| G21 / no root index | **MATCH** (STOP) | — |
| Army names in factory docs | **MATCH** (absent) | — |
| `plugins doctor` in WORKFLOW | **DRIFT** | blocker |
| Invented 0.14.0 in ship | **MATCH** (removed) | — |
| Invented 0.14.0 in spec | **DRIFT** | docs |

The next profile will be wrong if it copies `docs/PROFILE-PLAYBOOK.md` as it stands. HDR v2 code will not save that author. That is this slice’s fix list.
