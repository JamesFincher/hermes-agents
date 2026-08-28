# HDR audit 06 — claims + verify

**Base:** `main` @ `4019e7cf061c34f6f3d6b74025f66c4f1663aa07`  
**Slice:** quote-span provenance, `claim_verify`, claim graph, `conflict_report`, `cite_source` v2, verification pass including MoA-as-provider (not a toolset).  
**Spec sections:** §3.4, §3.5, §5.3 (`source_ledger_check` dies), `claim_verify` schema in §5.4, §7.4, plus HONEST-LIMITS on `claim_verify`.  
**Mode:** discovery first; implementation of §8 items 1–11 and 13–15 is in this PR. This file stays as the discovery record. Spec and playbook were not edited.

Classification: **MATCH** / **GAP** / **DRIFT** / **EXTRA** / **UNPROVEN**.  
Severity: **blocker** / **major** / **minor** / **docs**.

Hermes facts used here were re-checked against Context7 library `/nousresearch/hermes-agent` (Mixture of Agents page, Plugin LLM Access). Official MoA is provider `moa`, slash command `/moa`, config `moa.presets`. Official `moa_loop.py` states the slash command is “deliberately not a model tool.” Official `ctx.llm.complete` is the plugin LLM path. No Hermes knobs were invented.

---

## 0. Executive verdict

Mechanism 4 (`claim_verify`) exists as a registered deterministic tool and is **not** a rename of `source_ledger_check`. The plugin tool list, schemas, and skill copy all treat the old name as dead. That part of G05 is a **MATCH**.

The *algorithm* that G05 existed to kill — lexical overlap presented as verification — is **not gone**. It lives under a new name in `evals/gates.py:_unsupported_claims`. The live Citation Gate never calls `claim_verify`. `spans.verify_claim` itself relaxes “exact substring of the claim” into “any 8-word window.” Numeric consistency is set-intersection, not “every digit token in the claim appears in the span.” Offsets are Unicode string indexes, not file byte offsets. `unsupported_parts` is all-or-nothing.

Mechanism 5 (claim graph / `conflict_report`) has store types and a tool wrapper, but **no production writer**. `upsert_claim` is only called from the unit test and the offline eval harness. `conflict_report` therefore cannot emit tier-A disagreements or newest-vs-most-cited contradictions on a real run. The graph is not built as a side effect of any citation pass, because that pass does not exist in code.

§7.4 is a three-step verification pass. Step 2 (`claim_verify` sweep) is skill prose only. Step 1 (dedicated citation-mapping child or `ctx.llm`) is absent. Step 3 (MoA spot-check) is **not** a fake toolset — the skill correctly tells the operator to use the MoA *provider*. The automated spot-check itself is missing. That last item is a **GAP** whose fix is provider-path docs/skill (already started), not a `moa` toolset.

Honest limit on `claim_verify` is stated in spec, `docs/HONEST-LIMITS.md`, the profile README, and `claim-audit`. That is a **MATCH**, not a secret gap.

---

## 1. Spec quotes this audit is held to

### 1.1 §3.4 Quote-span provenance

> `source_ledger_check` dies. Its replacement, `claim_verify`, takes a claim and returns, per candidate source, an **exact substring match** against the stored corpus with byte offsets, plus a numeric-consistency check (do the digits in the claim appear in the span?), plus an entity check. A claim with no exact span in any corpus file is reported `unsupported`, and the Citation Gate (§5.7) refuses to let the brief be written while an unsupported claim carries a citation marker. Deterministic, zero inference tokens, and actually true — unlike overlap scoring.

### 1.2 §3.5 Claim Graph

> Every ledger entry links to claim nodes with a stance (`supports` / `contradicts` / `qualifies` / `silent`) and a confidence. `conflict_report` emits every claim where tier-A sources disagree, or where the newest source contradicts the most-cited one. … it is cheap because the graph is built as a side effect of the citation pass.

### 1.3 §5.3 Removed from v1

> `source_ledger_check` → `claim_verify` (**deleted, not renamed** — the overlap algorithm is gone).

### 1.4 §5.4 `claim_verify` schema

```
{"claim": "str", "candidate_sources": ["S17","S22"]}   # optional; defaults to all
# → {"status":"supported","evidence":[{"src":"S17","off":48213,"len":137,
#     "exact":true,"numeric_match":true,"span":"…"}],"unsupported_parts":[…]}
```

§5.2 also names the three-way status: `supported` / `partial` / `unsupported`.

### 1.5 §5.7 Citation Gate (the hook §3.4 points at)

> **Citation Gate**: on `write_file` / `patch` where the path is under the brief directory, parse the content for claim sentences and `[S#]` markers. Block if a marker is unresolvable in the ledger, or if a sentence containing a statistic, date, quantity, or quoted phrase carries no marker.

§3.4 and §5.7 are **not the same gate**. §3.4 requires a `claim_verify` refusal (unsupported *cited* claim). §5.7 requires marker-resolvability plus unmarked-stat refusal. The implementation implements §5.7 only.

### 1.6 §6.1 `claims.json`

> `{"C3": {"text": "…", "support": [{"src":"S17","stance":"supports","conf":0.9,"span":0}], "status":"contested|supported|unsupported"}}`

Ledger sources also carry `claims: ["C3", "C7"]`.

### 1.7 §7.4 Verification pass

> Three cheap passes, in order, after the draft exists:
>
> 1. **Citation pass** — a dedicated child (or `ctx.llm` `[UNV]`) that reads only the draft plus `evidence_search` output and maps every claim to card ids.
> 2. **`claim_verify` sweep** — deterministic exact-span check over the mapped claims. Anything `unsupported` goes back to phase 4 or gets cut.
> 3. **MoA spot-check** — run `mixture_of_agents` on the top three load-bearing claims … Optional at `standard`, required at `deep`+.

Official STOP (`docs/HERMES-FACTS.md`): there is no `moa` toolset and no `mixture_of_agents` tool. MoA verification, if used, is `/moa` or `/model … --provider moa`.

### 1.8 G11 (`cite_source` v2)

> `cite_source` formats APA/IEEE/Chicago from `url/title/quote`. Without author/date/container these citations are malformed. Fixed by §5.4 metadata extraction + Crossref.

### 1.9 Honest limit (admitted)

> `claim_verify` proves a span exists in a retrieved document. It does not prove the document is right, or that the span means what the claim says. It moves the failure mode from fabrication to misreading.

### 1.10 §10 gate this slice owns

> `claim_verify` unsupported in the final brief | 0

---

## 2. Inventory of files actually read

| Path | Why |
| --- | --- |
| `docs/HDR-SPEC.md` | Source of truth for §3.4, §3.5, §5.2–5.4, §5.7, §6.1, §7.4, §10, §13 |
| `docs/HERMES-FACTS.md` | Official STOP: no `moa` toolset |
| `docs/HONEST-LIMITS.md` | Admitted `claim_verify` limit |
| `agents/research-bot/plugins/hdr/tools/citation.py` | `claim_verify`, `conflict_report`, `cite_source` |
| `agents/research-bot/plugins/hdr/store/claims.py` | Claim graph |
| `agents/research-bot/plugins/hdr/store/spans.py` | `select_spans`, `verify_claim` |
| `agents/research-bot/plugins/hdr/hooks/output.py` | Deterministic bibliography |
| `agents/research-bot/plugins/hdr/hooks/policy.py` | Citation Gate |
| `agents/research-bot/plugins/hdr/hooks/prompt.py` | Phase-6 prompt text |
| `agents/research-bot/plugins/hdr/hooks/intake.py` | Span selection on intake; no claim upsert |
| `agents/research-bot/plugins/hdr/store/extract.py` | Author/date/container extraction |
| `agents/research-bot/plugins/hdr/store/ledger.py` | `claims[]` field, metadata columns |
| `agents/research-bot/plugins/hdr/store/bus.py` | Corpus offset semantics |
| `agents/research-bot/plugins/hdr/store/draft.py` | Deterministic brief + disagreement section |
| `agents/research-bot/plugins/hdr/tools/plan.py` | `gap_scan` conflict echo |
| `agents/research-bot/plugins/hdr/tools/evidence.py` | Intake twin; no claim linkage |
| `agents/research-bot/plugins/hdr/tools/retrieval.py` | `scholar_search` Crossref path |
| `agents/research-bot/plugins/hdr/scripts/crossref.py` | Skill-side Crossref; title/DOI/URL only |
| `agents/research-bot/plugins/hdr/schemas.py` | Model-facing `claim_verify` / `conflict_report` / `cite_source` |
| `agents/research-bot/plugins/hdr/plugin.yaml` | Tool + hook + `citation_style` |
| `agents/research-bot/plugins/hdr/__init__.py` | Registration |
| `agents/research-bot/plugins/hdr/runtime.py` | `WRITE_TOOLS`, HARD allowlist includes citation tools |
| `agents/research-bot/skills/claim-audit/SKILL.md` | Pre-publication loop |
| `agents/research-bot/skills/claim-audit/scripts/extract_claims.py` | Sentence splitter |
| `agents/research-bot/skills/deep-research-run/SKILL.md` | §7.4 operator instructions + MoA provider |
| `agents/research-bot/config.yaml` | No `moa` toolset; `citation_style: apa` |
| `agents/research-bot/README.md` | Tool table + honest limits |
| `agents/research-bot/INTEGRATION.md` | `ctx.llm` noted, not wired |
| `tests/test_hdr_plugin.py` | Claim / gate tests |
| `tests/test_hdr_eval_gates.py` | Fixture gates |
| `evals/gates.py`, `evals/rubric.py`, `evals/run_offline.py` | Deterministic “unsupported” check |
| `evals/fixtures/**` | Three fixture runs + recorded pages |
| `docs/PROFILE-PLAYBOOK.md` | Playbook still lists v1 ledger names (auditor 8) |

---

## 3. Mechanism 4 — `claim_verify` / quote-span provenance

### 3.1 Tool surface — MATCH (minor EXTRA)

`claim_verify` is registered on toolset `hdr` (`__init__.py:register`, `plugin.yaml` `provides_tools`, `schemas.CLAIM_VERIFY`). Handler is `citation.claim_verify`. Args: `claim` required, `candidate_sources` optional, defaults to all ledger sources. Return envelope includes `status`, `evidence[]`, `unsupported_parts`. Handler never raises; errors are `{"error": …}`. No LLM call. Deterministic. Zero inference tokens.

**EXTRA (minor):** response also includes `ok: True` and per-evidence `entity_match`. `entity_match` is required by §3.4 prose and missing from the §5.4 snippet. That is a schema-doc miss, not a code miss.

`schemas.CLAIM_VERIFY` description says “Not lexical overlap.” Correct advertising.

### 3.2 Exact substring match — DRIFT (blocker)

`spans.verify_claim` (`store/spans.py:60`):

1. `text.find(needle)` on the full claim. If found, `exact=True`. That *is* exact substring.
2. If not found, it searches contiguous windows of 12 down to 8 words of the claim. If any window hits, it **rewrites `needle` to that window** and sets `exact=True`.

```60:80:agents/research-bot/plugins/hdr/store/spans.py
def verify_claim(claim: str, corpus_text: str) -> dict[str, Any]:
    ...
    off = text.find(needle)
    exact = off >= 0
    if not exact:
        # try a long contiguous substring of 8+ words
        words = needle.split()
        for size in range(min(len(words), 12), 7, -1):
            ...
        exact = off is not None and off >= 0 and needle in text
```

§3.4: “an **exact substring match**” of the claim; “A claim with no exact span in any corpus file is reported `unsupported`.”

A 20-word claim that invents a conclusion after an 8-word quote is reported `exact: true`. That is the paraphrase-pass failure mode G05 named, only with a longer n-gram.

`citation.claim_verify` only appends evidence when `check.get("exact")` is true (`citation.py:36`). Status then becomes `supported` or `partial`, never `unsupported`, even if most of the claim is not in the corpus.

Claims shorter than 8 words and not present verbatim correctly stay `unsupported`. That sub-path is a MATCH.

### 3.3 Byte offsets — DRIFT (major)

Spec: “byte offsets into the corpus file.”  
§3.2 card shape: `"spans":[{"q":"…","off":48213,"len":137}]`.

Implementation:

- `bus.write_corpus` records both `bytes` (`len(body.encode("utf-8"))`) and `chars` (`len(body)`).
- `bus.read_corpus` slices with `text[start:end]` after `path.read_text(encoding="utf-8")` — **character** indexes.
- `verify_claim` / `select_spans` use `str.find` / `len(clipped)` — **character** indexes.

For ASCII fixtures this coincides with bytes. For any UTF-8 page (typical web extract) `off`/`len` are not file byte offsets. `evidence_read` then seeks with those same indexes (`evidence.py:111`). The pipeline is internally consistent and spec-wrong on the word “byte.”

### 3.4 Numeric-consistency check — DRIFT (major)

Spec: “do the digits in the claim appear in the span?”

```81:83:agents/research-bot/plugins/hdr/store/spans.py
    claim_nums = set(_NUM_RE.findall(claim or ""))
    span_nums = set(_NUM_RE.findall(text[off : off + len(needle)] if off is not None and off >= 0 else ""))
    numeric = (not claim_nums) or bool(claim_nums & span_nums)
```

This is **set intersection**, not subset. Claim `12% in 2024 and 87 units` against a span that only contains `12` is `numeric_match: true`. Empty digit sets pass (`not claim_nums`). Digits are taken from the *original* claim, but compared against the *possibly shortened* 8–12 word window, so a fabricated number outside the matched window can still pass if any other claim digit appears in the window.

`citation.claim_verify` requires `numeric_match` (and `entity_match`) on **every** evidence row to promote `partial` → `supported` (`citation.py:50`). A single sloppy source can therefore keep a multi-source claim at `partial`, which is conservative. The per-row predicate itself is still too weak.

### 3.5 Entity check — DRIFT (major)

```84:86:agents/research-bot/plugins/hdr/store/spans.py
    entities = {t.lower() for t in _WORD_RE.findall(claim or "") if t[:1].isupper() and len(t) > 2}
    blob = (text[off : off + max(len(needle), 200)] if off is not None and off >= 0 else text[:400]).lower()
    entity = (not entities) or any(name.lower() in blob for name in entities)
```

What it does:

- Title-case tokens longer than 2 characters. Sentence-initial `The`, `This`, `However` become “entities.”
- Match is `any`, not `all`. One of N names is enough.
- If there is no span (`off` missing), it still scores entities against `text[:400]`. `claim_verify` currently drops non-exact rows, so this branch is dead for the tool — but `verify_claim` itself will report `entity_match: true` against the front of the page.

Spec §3.4 only says “plus an entity check.” No algorithm is given. The existence of *a* check is MATCH; the check is too weak to carry the word “entity.” Severity major because it participates in the `supported` decision.

### 3.6 `unsupported_parts` — DRIFT (minor)

§5.4 returns `unsupported_parts: […]`. The name implies decomposition.

`citation.claim_verify` initializes `unsupported_parts = [claim]` and sets it to `[]` only when status is `supported` (`citation.py:24`, `52`). `partial` still returns the entire claim as the only “part.” No span-level leftover, no missing-digit list, no unmatched entity list.

### 3.7 Status mapping — MATCH with a caveat

| Condition | Status |
| --- | --- |
| No exact evidence row | `unsupported` |
| ≥1 exact row, not all numeric∧entity | `partial` |
| ≥1 exact row, all numeric∧entity | `supported` |

§5.2 asked for this three-way enum. MATCH.

Caveat: because of the 8-word fallback, `supported` does not mean “the claim is an exact substring of a corpus file.”

Sources with empty `corpus` are skipped (`citation.py:29`). A cited card that never entered the bus cannot support a claim. MATCH for “against the stored corpus.”

### 3.8 Candidate source filter — MATCH

`candidate_sources` filters `ledger.list_sources()` by id (`citation.py:18-22`). Omitted or non-list → all sources.

### 3.9 Citation Gate × unsupported cited claims — GAP (blocker)

§3.4: the Citation Gate “refuses to let the brief be written while an unsupported claim carries a citation marker.”

`policy._citation_gate` (`hooks/policy.py:277`):

1. Runs only on `WRITE_TOOLS` (`write_file`, `patch`) under `BRIEF_DIRS`. MATCH vs §5.7 surfaces.
2. Blocks `[S#]` not in `ledger.list_sources()`. MATCH vs §5.7 unresolvable markers.
3. Blocks sentences matching `_STAT_RE` (percent, years, grouped numbers, quoted phrases) that lack an `[S#]`. MATCH vs §5.7 unmarked stats/quotes.
4. **Never calls `claim_verify`.** **Never reads the corpus.** **Never inspects `unsupported`.**

A brief that says `Growth was 99% [S1].` where S1 exists and the corpus says `Growth was 12%` is **allowed**. That is the exact §3.4 refusal the mechanism exists to enforce.

`test_dedupe_and_citation_gate` only asserts unresolvable `S99` is blocked (`tests/test_hdr_plugin.py:216`). No test writes a resolvable `[S#]` on a claim that fails exact-span.

`transform_llm_output` (`hooks/output.py`) flags uncited stats in chat. That is the documented mitigation for the honest-limit “chat bypasses the file-write gate.” It does **not** close the unsupported-cited-claim hole.

### 3.10 `source_ledger_check` deletion — MATCH in plugin/skills/tests; DRIFT in playbook; reincarnation in evals

| Location | `source_ledger_check`? |
| --- | --- |
| Registered tools (`__init__.py`, `plugin.yaml`, `schemas.py`) | Absent. `test_register_surfaces` asserts `assertNotIn("source_ledger_check", names)`. |
| Plugin store / tools | No function, no alias, no overlap scorer named that. |
| `claim-audit/SKILL.md` | “`source_ledger_check` is gone. Do not look for it.” Factory validator *requires* that sentence (`scripts/validate_factory.py:734`). |
| Profile README | “`source_ledger_check` is gone.” |
| `evals/fixtures/questions.json` | Historical: “G05 was lexical overlap. claim_verify replaces source_ledger_check…” |
| `docs/PROFILE-PLAYBOOK.md:529` | Still lists `source_ledger_add`, `source_ledger_list`, `cite_source`, `source_ledger_check` as the research-bot ledger tools. **Docs drift. Playbook is owned by auditor 8.** |

§5.3 says the overlap *algorithm* is gone, “not renamed.”

`evals/gates.py:_unsupported_claims` (`67-90`):

```python
        claim = _SID.sub("", sentence).strip()
        words = [w for w in re.findall(r"[A-Za-z0-9%]{4,}", claim)]
        ...
            if any(word.lower() in text.lower() for word in words[:6]):
                supported = True
```

That is lexical overlap of the first six 4+ character tokens, case-insensitive, anywhere in the source corpus. It does not call `claim_verify`. It does not require an exact span. It does not check digits or entities.

Proof on fixture `run_a`:

- Brief sentence: `The official Mixture of Agents page says there is no moa toolset [S1].`
- S1 corpus (`evals/fixtures/run_a/corpus/s1.txt`): `MoA is no longer listed under hermes tools; there is no moa toolset to enable.`
- Exact claim text is **not** in the corpus. `claim_verify` on that sentence would be `unsupported` (or, if the 8-word window hits a different source, still not this sentence).
- Gate tokens include `there` (and `official`/`page`/`says`…). `there` appears in the corpus. Gate **passes**.

`test_three_fixture_runs_pass_gates` therefore cannot enforce the §10 row “`claim_verify` unsupported in the final brief | 0”. `test_twelve_questions_complete_offline` goes further and passes `gate_errors=[]` into `score_brief`, so the offline 12-question loop never scores citation validity against this gate at all.

**This is lexical overlap under a new name.** Severity **blocker** for the G05 “algorithm is gone” claim.

`select_spans` (`spans.py:20-32`) also scores sentences by query-token overlap. That is Evidence Bus *selection* (§3.2 “most relevant to the active question”), not verification. Noted so nobody “fixes” the wrong function. It is not a `source_ledger_check` rename.

### 3.11 Tests for Mechanism 4 — GAP (major)

`tests/test_hdr_plugin.py:test_claim_verify_and_conflicts`:

- Corpus text **is** the claim (`text = "The device reached 12% efficiency in 2024 at NIST."`).
- Asserts `status == "supported"`.
- Does not assert `off`, `len`, `exact`, `numeric_match`, `entity_match`, `unsupported_parts`, or `candidate_sources`.
- Does not test paraphrase → `unsupported`.
- Does not test numeric miss → `partial`.
- Does not test entity miss → `partial`.
- Does not test the 8-word fallback.
- Does not test Citation Gate + unsupported cited claim.

`tests/test_hdr_eval_gates.py` never imports `claim_verify`. It only runs `evals.gates.check_run` on fixtures.

There is no unit test of `spans.verify_claim` in isolation.

### 3.12 Honest limit — MATCH (docs)

Stated verbatim (or near-verbatim) in:

- `docs/HDR-SPEC.md` §13
- `docs/HONEST-LIMITS.md`
- `agents/research-bot/README.md` Honest limits
- `agents/research-bot/skills/claim-audit/SKILL.md` Pitfalls

This is an admitted limit, not a hidden gap. The implementation does not claim semantic entailment. Good.

---

## 4. Mechanism 5 — Claim Graph and `conflict_report`

### 4.1 Store shape — MATCH (partial)

`store/claims.py`:

- Path: `plugin-data/hdr/claims.json` via `plugin_data_root()`. MATCH vs §5.5.
- Stances: `supports` / `contradicts` / `qualifies` / `silent`. MATCH vs §3.5.
- Node: `{text, support:[{src, stance, conf, span}], status}`. MATCH vs §6.1.
- Status: `contested` if both `supports` and `contradicts` are present; else `supported` if any `supports`; else `unsupported`. `qualifies` / `silent` never create `contested`.
- Identity is **exact `text` equality** (`upsert_claim` `node.get("text") == claim_text`). Paraphrases of the same proposition become distinct nodes. Spec does not define merge, so this is MATCH-by-silence and operationally weak.
- Unknown stance is coerced to `supports` (`claims.py:58-59`). Silent data loss.

Ledger rows have a `claims: []` field (`ledger.add_source`, `migrate_v1`). **Nothing in production writes Cids into it.** §3.5 “Every ledger entry links to claim nodes” is therefore a **GAP**.

### 4.2 No production writer — GAP (blocker)

`upsert_claim` callers in this checkout:

| Caller | Production? |
| --- | --- |
| `tests/test_hdr_plugin.py:test_claim_verify_and_conflicts` | No |
| `evals/run_offline.py` (only when `kind == "contradiction"`) | Harness only |

Not called from: `claim_verify`, `cite_source`, `conflict_report`, intake, `evidence_add`, `gap_scan`, `transform_llm_output`, skills scripts, hooks.

There is **no registered tool** that inserts a claim node. The model cannot populate the graph. `write_file` cannot reach `plugin-data/` (write allowlist is `notes/ research/ briefs/ findings/ citations/ sources/ data/`).

§3.5: “the graph is built as a side effect of the citation pass.” There is no citation pass in code (see §5 below). The side effect therefore cannot exist.

### 4.3 `conflict_report` — DRIFT (major)

`citation.conflict_report` dumps `claims.conflicts()`:

```92:100:agents/research-bot/plugins/hdr/store/claims.py
def conflicts() -> list[dict[str, Any]]:
    ...
        if node.get("status") == "contested":
            out.append({"id": cid, **node})
```

Spec §3.5 requires emission when:

1. **tier-A sources disagree**, or
2. **the newest source contradicts the most-cited one**.

Implementation:

- Does not read ledger tiers.
- Does not compare publish dates.
- Does not count how often a source is cited.
- Does not treat `qualifies` vs `supports` as disagreement.
- Does not attach source tier to the row (spec §5.2: “with stance and tier”). Stance is on the support edge; tier is absent.

On a real run the tool returns `{ok, count: 0, conflicts: []}`. Tests pass only because they call `upsert_claim` twice by hand (`S1 supports` + `S2 contradicts` on text `"efficiency"`).

`gap_scan` echoes the same empty list as `conflicts` (`plan.py:91`, `114`). `draft.draft_brief` will render a “Disagreement / Do not average” section **if** the graph is populated (`draft.py:39-43`). That helper is the right instinct and is currently unreachable in production.

### 4.4 “Do not average” — MATCH (docs / prompt), UNPROVEN (runtime)

Prompt section `hdr.method` (`hooks/prompt.py:17`): “6 VERIFY: claim_verify, conflict_report, cite_source. Do not average.”  
`claim-audit` and `deep-research-run` repeat it.  
`draft.draft_brief` literally writes “sources disagree. Do not average.”

Runtime averaging of contested claims does not exist as a function — there is nothing to average because the graph is empty. **UNPROVEN** that a live run will surface disagreement rather than blend it. The synthesizer is still a model reading cards.

### 4.5 Tests for Mechanism 5 — GAP (major)

The only conflict test is the hand-seeded `upsert_claim` pair. No test for:

- tier-A vs tier-C disagreement (should emit per spec; current code emits any `supports`+`contradicts` regardless of tier — which would be EXTRA if the graph were populated, and is still the wrong predicate)
- newest-vs-most-cited
- empty graph on a two-source contradiction fixture (`run_a` ledger has S1 vs S2 on MoA toolset existence; `claims.json` is not even in the fixture directory)

---

## 5. §7.4 Verification pass

### 5.1 Step 1 — Citation pass (dedicated child or `ctx.llm`) — GAP (major)

Spec: a pass *separate from synthesis* that maps every claim to card ids, via a dedicated child or `ctx.llm`.

Context7 `/nousresearch/hermes-agent` Plugin LLM Access: `ctx.llm.complete` / `complete_structured` is the supported out-of-band plugin LLM. `docs/HERMES-FACTS.md` resolved the spec `[UNV]` to `[DOC]`. `INTEGRATION.md` line 87: “Official Plugin LLM Access. Out of band. Trust-gated. Optional citation pass. Not a substitute for `claim_verify`.”

**No plugin code calls `ctx.llm`.** Grep hits are docs and the factory string list only.

No `worker_brief` / `delegate_task` template exists for a citation-mapping child. `deep-research-run` tells the orchestrator to “Verify with `claim_verify` and `conflict_report`” in the same breath as synthesis follow-up. That is inline, not a separate pass.

`claim-audit/scripts/extract_claims.py` splits sentences (skip short, headings, tables, tiny hedges). It does not map claims to `[S#]`. The *model* is expected to call `claim_verify` per line. That is a prompt loop, which is what G15 said v1 already had (`claim-check` is a prompt).

### 5.2 Step 2 — `claim_verify` sweep — DRIFT (major)

Skill-mandated, not enforced:

- `deep-research-run` Verification: “`claim_verify` has no unsupported load-bearing claim.”
- `claim-audit` Verification: “Zero `claim_verify` status `unsupported` on remaining cited claims.”
- Citation Gate does not run the sweep.
- `evals/gates.py` does not run the sweep (it runs overlap).
- `evals/run_offline.py` calls `claim_verify` once on `brief.split(".", 1)[0]` and **does not fail the run** on `unsupported`.

“Anything `unsupported` goes back to phase 4 or gets cut” is operator prose only.

### 5.3 Step 3 — MoA spot-check — GAP (spot-check missing) + MATCH (no fake toolset)

**Official STOP (reconfirmed via Context7):**

- Mixture of Agents page: `/moa`, `/model … --provider moa`, `moa.presets`.
- CLI: `hermes moa list|configure|delete`.
- `moa_loop.py`: “The slash command is deliberately not a model tool.”
- Toolsets reference: no `moa` toolset.
- `docs/HERMES-FACTS.md` STOP: “Do not invent a replacement toolset.”

**What the tree does (correct):**

- `agents/research-bot/config.yaml` omits `moa` from `custom_toolsets.research` and comments the STOP.
- `validate_factory.py:434` fails the profile if `moa` is bundled.
- `deep-research-run/SKILL.md:49`: “At `deep` or `exhaustive`, ask the operator for a MoA second opinion on the top three load-bearing claims. Official MoA is provider `moa` (`/moa` or `/model … --provider moa`). There is no `moa` toolset and no `mixture_of_agents` tool.”
- README, HONEST-LIMITS, smoke `P1-LIVE.md` all say there is no `moa` toolset.
- No `mixture_of_agents` handler. No invented `moa` toolset. Code does **not** silently pretend a toolset exists.

**What is missing (GAP, not a toolset):**

- No automated “top three load-bearing claims” selection.
- No hook or skill script that invokes `/moa` or switches provider.
- Optional-at-standard / required-at-`deep`+ is not enforced by the governor, `gap_scan`, or Citation Gate.
- Spec §4.2 still lists `moa` in the example bundle; P1 acceptance still says `/tools list` shows `moa`; §7.4 still says `run mixture_of_agents`. Those spec lines are **docs DRIFT** against the official STOP. The *implementation* followed HERMES-FACTS, not those stale spec lines. That is the right direction.

**Fix path (do not apply here):** keep MoA as provider; tighten skill/docs so `deep`+ runs actually perform the operator `/moa` spot-check (or a `ctx.llm` call that does not invent a toolset). Do not add a `moa` toolset.

### 5.4 `/review` — UNPROVEN

§7.4 last sentence: “`/review` can be pointed at the finished brief… pin `auxiliary.review`.” Not this slice’s core, and no code in the citation package implements it. Not scored as a claim-verify GAP.

---

## 6. `cite_source` v2 (G11: author / date / container)

### 6.1 Formatter — PARTIAL MATCH (major remaining GAP)

`citation._format` (`citation.py:111`) reads `authors`, `published`/`retrieved` (year via `(20|19)\d{2}`), `publisher`, `title`, `canonical_url`/`url`.

| Style | Author | Date | Container |
| --- | --- | --- | --- |
| default APA-ish | first 3 authors, comma-joined | `(year).` | `publisher.` |
| IEEE | author + title + year + URL | year | **omitted** |
| Chicago | author + quoted title + `(year)` | year | `publisher.` |

If authors/date/publisher are empty, the formatter still emits `title. url` (or IEEE `title. url`). G11’s “malformed without author/date/container” is **not refused**. There is no `container` field distinct from `publisher`. `extract.extract_metadata` maps `citation_journal_title` into `publisher` (`extract.py:62-63`). That is a collapse, not a container.

`cite_source` does **not** call Crossref, Unpaywall, or `scripts/crossref.py` at format time. Missing metadata stays missing.

`transform_llm_output` uses `cite_source` for the deterministic `## Sources` block (`output.py:28`). Zero inference tokens. MATCH vs §5.7 bibliography sentence. It inherits the same malformed rows.

### 6.2 Metadata extraction — PARTIAL MATCH

`store/extract.py` pulls JSON-LD Article, OpenGraph, `citation_*`, DOI, `<title>`, a YYYY-MM-DD regex. Intake (`hooks/intake.py:125-130`) and `evidence_add` write `authors`, `publisher`, `published`, `doi` onto the ledger. This is the §3.2 / G11 extraction path and it is real.

Gaps:

- No `container` / `journal` column on the ledger schema (§6.1 lists `publisher`, not container).
- `scholar_search` (`retrieval.py:144-157`) hits Crossref HTTP but **drops** Crossref authors, container-title, and publisher when calling `ledger.add_source`. `published` is `str((item.get("issued") or {}).get("date-parts") or "")` (e.g. `[[2024, 6, 1]]`), which `_format`’s year regex may still scrape, badly. Publisher is returned on the *card* and not stored on the *row*.
- `plugins/hdr/scripts/crossref.py` (and the literature-sweep copy) returns `{title, doi, url}` only — not author, date, or container. Useless for G11 backfill.

### 6.3 Tests — GAP (minor)

`test_claim_verify_and_conflicts` only asserts `cite["count"] >= 1`. No APA/IEEE/Chicago golden strings. No “author present” assertion. Fixture ledgers (`run_a`, `run_b`, `run_c`) omit `authors` entirely. A bibliography appended from those fixtures is title + URL.

---

## 7. Skills and operator path

### 7.1 `claim-audit` — MATCH for the skill contract; cannot close the code gaps

Frontmatter: `requires_tools: [claim_verify, conflict_report, cite_source]`. Disjoint trigger. Script via `${HERMES_SKILL_DIR}`. Procedure: extract → `claim_verify` each → cut unsupported citations → `conflict_report` → `cite_source`. Honest limit stated. `source_ledger_check` declared gone.

`extract_claims.py` is a deterministic sentence splitter, not a claim/span mapper. That matches §6.4 “`extract_claims.py` + `claim_verify` loop” as a *skill*, not as a gate.

### 7.2 `deep-research-run` — DRIFT vs §7.4, MATCH vs official MoA STOP

Phase 6 in Quick Reference is “`claim_verify` and `cite_source`” (no citation-pass child). Procedure describes the Citation Gate as blocking unresolvable markers and unmarked statistics — honest about the implemented gate, silent about §3.4’s unsupported-cited-claim rule. MoA paragraph is the correct provider-path instruction.

`hdr.method` prompt (`prompt.py:17`) same three tools, no MoA, no `ctx.llm`.

---

## 8. Findings table

| # | Finding | Class | Sev | Spec | Code |
| --- | --- | --- | --- | --- | --- |
| F01 | `claim_verify` is a new tool; `source_ledger_check` is not registered | MATCH | — | §5.3 | `citation.claim_verify`, `test_register_surfaces` |
| F02 | Exact match relaxed to 8–12 word windows | DRIFT | blocker | §3.4 exact substring | `spans.verify_claim` |
| F03 | Offsets are Unicode indexes, not file bytes | DRIFT | major | §3.4 / §3.2 “byte offsets” | `spans.py`, `bus.read_corpus` |
| F04 | Numeric check is intersection, not “all digits in the span” | DRIFT | major | §3.4 | `spans.verify_claim` numeric |
| F05 | Entity check is title-case `any` + sentence-initial false positives | DRIFT | major | §3.4 | `spans.verify_claim` entity |
| F06 | `unsupported_parts` is `[claim]` or `[]` | DRIFT | minor | §5.4 | `citation.claim_verify` |
| F07 | Three-way status + optional `candidate_sources` | MATCH | — | §5.2 / §5.4 | `citation.claim_verify` |
| F08 | Citation Gate does not refuse unsupported *cited* claims | GAP | blocker | §3.4 → §5.7 | `policy._citation_gate` |
| F09 | §5.7 unresolvable-marker + unmarked-stat gate exists | MATCH | — | §5.7 | `policy._citation_gate` |
| F10 | Lexical overlap lives on as `evals.gates._unsupported_claims` | DRIFT | blocker | §5.3 “overlap algorithm is gone” | `evals/gates.py:67` |
| F11 | Playbook still lists `source_ledger_check` | DRIFT | docs | §5.3 | `docs/PROFILE-PLAYBOOK.md:529` (auditor 8) |
| F12 | Claim graph has no production writer; ledger `claims[]` unused | GAP | blocker | §3.5 / §6.1 | `claims.upsert_claim` callers |
| F13 | `conflict_report` is `status==contested` only; no tier-A / newest-vs-most-cited | DRIFT | major | §3.5 / §5.2 | `claims.conflicts` |
| F14 | “Do not average” is prompt/skill only | UNPROVEN | major | §3.5 | prompt + skills |
| F15 | §7.4 citation-mapping pass (`ctx.llm` or child) absent | GAP | major | §7.4.1 | no `ctx.llm` usage |
| F16 | `claim_verify` sweep is skill prose, not a gate | DRIFT | major | §7.4.2 / §10 | skills; `run_offline.py` ignores status |
| F17 | No `moa` toolset invented; skill names the provider | MATCH | — | HERMES-FACTS STOP | `config.yaml`, `deep-research-run` |
| F18 | MoA spot-check is not executed by code | GAP | major | §7.4.3 | none (fix = provider path, not a toolset) |
| F19 | Spec §4.2 / P1 / §7.4 still say toolset `moa` / `mixture_of_agents` | DRIFT | docs | vs HERMES-FACTS | `docs/HDR-SPEC.md` |
| F20 | `cite_source` can emit author/date/publisher when present | MATCH | — | G11 | `citation._format` |
| F21 | No container field; IEEE drops publisher; no Crossref backfill at cite time; scholar_search drops Crossref authors | GAP | major | G11 | `citation._format`, `retrieval.scholar_search`, `scripts/crossref.py` |
| F22 | Honest limit on `claim_verify` is published | MATCH | — | §13 | HONEST-LIMITS, README, claim-audit |
| F23 | Unit tests only cover happy-path exact clone of the corpus | GAP | major | P7 / §10 | `test_claim_verify_and_conflicts` |
| F24 | `entity_match` extra field on evidence rows | EXTRA | minor | §3.4 yes / §5.4 snippet no | `citation.claim_verify` |
| F25 | `select_spans` uses overlap for *relevance*, not verification | EXTRA | docs | §3.2 | `spans.select_spans` — do not treat as G05 |

---

## 9. Fixture / eval walk (claim gates only)

### 9.1 `run_a` (contradiction)

Brief names the MoA disagreement in prose and cites S1/S2/S3. Corpus texts do **not** contain those brief sentences. Overlap gate passes (`there`, `toolset`, `lists`, …). `claim_verify` on the first sentence would not find an exact span. Fixture `audit.json` has no claim-graph file. This fixture does **not** prove Mechanism 4 or 5.

### 9.2 `run_b` (paywall)

`The fixture paper abstract states the method reached 12% efficiency in 2024 [S1].` vs corpus `We show the method reached 12% efficiency in 2024 under the fixture protocol.` Overlap (`method`, `reached`, `efficiency`, `2024`) passes. Exact claim string is absent. Same hole.

### 9.3 `run_c` (dead link)

`The 2023 Wayback snapshot said the product launched in March [S1].` vs `We announced the product launched in March after a quiet beta.` Overlap (`product`, `launched`, `March`) passes. Exact claim string is absent.

### 9.4 Offline 12-question loop

`evals/run_offline.py` seeds the contradiction graph by hand, verifies only the first sentence of `draft_brief()`, and `test_hdr_eval_gates.py` scores those briefs with `gate_errors=[]`. P7 acceptance (“every deterministic gate in §10 passes on 3 fixture runs”) is green for the **overlap** gate, not for `claim_verify`.

---

## 10. Numbered fix list (do not apply)

These are recommendations for a later implementation pass. This audit does not implement them.

1. **Delete the 8–12 word fallback** in `spans.verify_claim`. `exact` means `corpus.find(claim) >= 0` (or a documented quote-normalized exact, e.g. whitespace-collapsed, still the whole claim). No exact span → `unsupported`.
2. **Define numeric as subset**, not intersection: every digit token in the claim must appear in the *matched span*. Missing digits → `partial` and list them in `unsupported_parts`.
3. **Define entity as all retained names**, with a stop-list for sentence-initial function words. Missing names → `partial` + `unsupported_parts`.
4. **Store and return byte offsets** (`text.encode("utf-8")` slice / `bytes.find`) *or* amend the spec to “character offsets” and make `evidence_read` / cards use the same unit everywhere. Do not mix.
5. **Make `unsupported_parts` real**: unmatched clauses, missing digits, missing entities. Empty only when `supported`.
6. **Wire Citation Gate to `claim_verify`**: on brief-path `write_file`/`patch`, for every sentence that carries `[S#]`, run `claim_verify` (optionally restricted to those ids). If status is `unsupported`, block and quote the sentence. Keep the existing unresolvable-marker and unmarked-stat rules.
7. **Replace `evals.gates._unsupported_claims`** with a call to `spans.verify_claim` / `citation.claim_verify` against fixture corpora. A paraphrase must fail. Fixture briefs that are not exact spans must be rewritten or the gate must fail them.
8. **Stop passing `gate_errors=[]`** in `test_twelve_questions_complete_offline`. Score the real gate.
9. **Add unit tests**: paraphrase → unsupported; 8-word prefix of a longer fabricated claim → unsupported; numeric miss → partial; entity miss → partial; offsets; `candidate_sources`; Citation Gate refuse of `12% [S1]` when corpus has `14%`; `source_ledger_check` remains unregistered.
10. **Give the claim graph a writer.** Cheapest deterministic path: after a successful `claim_verify`, `upsert_claim` with stance `supports` and the span index; expose an optional `stance` arg for the model or for the citation pass. Write Cids onto `ledger.sources[].claims`.
11. **Implement `conflicts()` per §3.5**: emit when two tier-A edges disagree, *or* when the newest source (by `published`/`retrieved`) contradicts the most-cited source. Attach `tier` on each support edge. Do not average; keep `draft.draft_brief`’s “Disagreement” section.
12. **Do not invent a claims-average tool or a `moa` toolset.**
13. **Citation pass:** either a `worker_brief` mandate that returns claim→`[S#]` JSON, or a single `ctx.llm.complete_structured` call (official, trust-gated, purpose-tagged). Then run the `claim_verify` sweep in code over that map. This is §7.4.1–2. Do not put the sweep only in SKILL.md.
14. **MoA spot-check:** keep provider path. Skill already names `/moa`. Add a verification checkbox that is empty until the operator (or a later `ctx.llm` call that does not register a tool) records the three-claim spot-check at `deep`+. Update spec §4.2 / P1 / §7.4 to delete `moa` toolset and `mixture_of_agents`.
15. **`cite_source` v2:** persist Crossref `author`, `issued`, `container-title` in `scholar_search` and in `scripts/crossref.py`. Add `container` (or stop collapsing `journal_title` into `publisher`). IEEE should not drop container. Optionally refuse to emit a styled citation that lacks author+date when the style requires them, and surface `needs_backfill`.
16. **Playbook (auditor 8):** replace the v1 ledger row (`source_ledger_*`) with `evidence_*` / `claim_verify`. This audit does not edit that file.
17. **Do not treat `select_spans` overlap as G05.** If someone “removes all overlap,” they will break Evidence Bus relevance ranking. Verification and selection are different functions.

---

## 11. What this audit is not

- Not an Evidence Bus / intake audit except where span offsets and metadata feed verify/cite.
- Not a Budget Governor audit.
- Not a playbook rewrite (F11 is noted for auditor 8).
- Not an implementation. No production file was edited.

---

## 12. Bottom line

`claim_verify` is a real, deterministic, zero-token tool, and `source_ledger_check` is gone from the plugin. The *promise* of Mechanism 4 — exact span + digits + entities, Citation Gate refuse of unsupported citations, overlap algorithm dead — is not kept. The eval gate that is supposed to prove it is the old overlap scorer under a new function name.

The claim graph is a typed store with no writer. `conflict_report` cannot surface disagreement on a live run. §7.4’s citation pass is missing. MoA is correctly *not* a toolset; the spot-check is missing as an operator/provider step, which is the allowed GAP shape.

Honest limit: `claim_verify`, even when exact, still only proves a span exists. That sentence is already in the shipped docs. The larger problem is that today’s `supported` does not even reliably prove the span exists.
