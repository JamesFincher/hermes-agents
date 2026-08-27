# HDR audit 02 — plugin + tools

**Base:** `main` @ `4019e7cf061c34f6f3d6b74025f66c4f1663aa07`  
**Slice:** native plugin package + tool inventory + schemas + handlers.  
**Spec:** `docs/HDR-SPEC.md` §4.4, §5.1, §5.2, §5.3, §5.4, plus plugin/tool rules in `docs/HERMES-FACTS.md`.  
**Mode:** discovery only. No production code was changed. This file is the only deliverable.

A second engineer should be able to implement the numbered fix list at the end without re-opening the plugin.

---

## 0. Method and classification

Read, line-by-line:

- `docs/HDR-SPEC.md` (Claude source of truth; v1 superseded)
- `docs/HERMES-FACTS.md` (official Hermes probe, 2026-08-27)
- `agents/research-bot/plugins/hdr/plugin.yaml`
- `agents/research-bot/plugins/hdr/__init__.py`
- `agents/research-bot/plugins/hdr/runtime.py`
- `agents/research-bot/plugins/hdr/schemas.py`
- `agents/research-bot/plugins/hdr/tools/__init__.py`
- `agents/research-bot/plugins/hdr/tools/plan.py`
- `agents/research-bot/plugins/hdr/tools/evidence.py`
- `agents/research-bot/plugins/hdr/tools/citation.py`
- `agents/research-bot/plugins/hdr/tools/fanout.py`
- `agents/research-bot/plugins/hdr/tools/retrieval.py`
- `agents/research-bot/config.yaml` — only `plugins.enabled` and `custom_toolsets`

Store helpers were opened only where a handler’s live return shape is defined by them (`store/run.py`, `store/ledger.py`, `store/bus.py`, `store/spans.py`, `store/claims.py`, `store/index.py`). Hooks and skills are out of scope except where a tool’s contract depends on them (claim graph write path, `cite_source` used by `transform_llm_output`).

Official handler contract was re-checked via Context7 library `/nousresearch/hermes-agent` (live docs 2026-08-27) and `HERMES-FACTS.md` §13 / §19:

1. `handler(args, **kwargs)`
2. Return `json.dumps` string. Never a dict.
3. Errors `{"error": "..."}`.
4. Never raise.
5. `task_id = kwargs.get("task_id")`.

**Classes**

| Class | Meaning |
| --- | --- |
| **MATCH** | Live code implements the spec/facts contract. |
| **GAP** | Spec/facts require it; live code is missing or incomplete. |
| **DRIFT** | Something exists but the algorithm, schema, or return shape differs from spec. |
| **EXTRA** | Live code adds a surface, field, or behavior the spec does not ask for. |
| **UNPROVEN** | Cannot be closed from source + official docs alone (needs a live Hermes 0.19.0 host). |

**Severity:** `blocker` (loop or verification is false), `major` (wrong contract the model or a later fixer will rely on), `minor` (fixable without changing the research loop), `docs` (spec/facts disagree with each other or with live; do not invent a knob).

Surfaces are not collapsed: this file audits the **plugin host package** (`plugin.yaml` + `register(ctx)`) and the **tools** (registry schema + handler). Skills, MCP servers, and hooks are named only when a tool’s contract depends on them.

---

## 1. Package, toolset, and `register(ctx)`

### 1.1 Layout vs spec §4.4

Spec §4.4 tree (tools + host files only):

```
plugins/hdr/
  plugin.yaml
  __init__.py
  runtime.py
  schemas.py
  tools/plan.py, evidence.py, citation.py, retrieval.py, fanout.py
```

**MATCH.** All of those files exist. Additional package files exist (`hooks/`, `store/`, `scripts/`, `tools/__init__.py`). Those are in-spec for the plugin as a host package; they are not extra *tools*. `store/draft.py` is not in the §4.4 tree — **EXTRA** for the package, not a registered tool. No `plugin.json` (portable v1 path). Comments in `plugin.yaml` and `__init__.py` correctly say native `plugin.yaml` + `register(ctx)`.

Profile name stays `research-bot` (`agents/research-bot/`, `distribution.yaml` `name: research-bot`). Plugin / toolset id is `hdr`. **MATCH** the naming rule (profile ≠ plugin ≠ toolset).

### 1.2 Toolset id

| Surface | Value | Class |
| --- | --- | --- |
| `runtime.PLUGIN_ID` | `"hdr"` | MATCH |
| `runtime.TOOLSET` | `"hdr"` | MATCH |
| `plugin.yaml` `name` | `hdr` | MATCH |
| `register()` `toolset=` | `runtime.TOOLSET` (`"hdr"`) | MATCH |
| `config.yaml` `custom_toolsets.research` | includes `hdr`; no `moa`; no `research-bot`; no `army` | MATCH vs facts STOP |
| `config.yaml` `plugins.enabled` | `[hdr]` | MATCH |
| `config.yaml` `plugins.entries.hdr` | present, `mcp_allowlist: [context7]` | MATCH vs facts |

Grep of `agents/research-bot/plugins/hdr/**/*.py` finds **zero** `source_ledger_*`, **zero** `army`, **zero** `toolset="research-bot"`. User-Agent strings contain `hdr-research-bot/2.0` (HTTP client name, not a toolset). **MATCH.**

Do **not** reintroduce toolset `research-bot` or `army` / `army-runtime`. Official STOP: no `moa` toolset (MoA is a provider). Live `config.yaml` already follows facts, not the stale `moa` / `openalex` / `pubmed` / `wayback` rows still printed in spec §4.2. That spec-vs-facts mismatch is **docs**, not a code defect.

### 1.3 `register(ctx)` actually registers every schema

```53:62:agents/research-bot/plugins/hdr/__init__.py
def register(ctx: Any) -> None:
    runtime.set_ctx(ctx)
    for schema in schemas.ALL:
        name = str(schema["name"])
        ctx.register_tool(
            name=name,
            toolset=runtime.TOOLSET,
            schema=schema,
            handler=_HANDLERS[name],
        )
```

AST check on this commit:

- `plugin.yaml` `provides_tools` = 15 names
- `schemas.ALL` name fields = the same 15, same order
- `_HANDLERS` keys = the same 15
- `tools/__init__.py` `__all__` = the same 15
- v1 names `source_ledger_add`, `source_ledger_list`, `source_ledger_check` are absent from all three

**MATCH.** If a future schema is appended to `ALL` without a `_HANDLERS` entry, `register()` raises `KeyError` at load (host-time, not handler-time). There is no guard. **UNPROVEN** whether a live Hermes 0.19.0 host accepts the flat `{name, description, parameters}` schema object; that is the official adding-tools / plugins shape, so treat as MATCH unless a later host probe fails.

`register()` also registers hooks and `hooks.register_sections(ctx)`. Out of tool-inventory scope. Hook names in `plugin.yaml` `provides_hooks` match the `ctx.register_hook(...)` calls.

### 1.4 Handler contract (all 15)

| Rule | Live | Class |
| --- | --- | --- |
| Accept `args` + `**kwargs` | All 15 public handlers | MATCH |
| Return JSON string via `runtime.dump` / `runtime.error` | All return paths are `dump(...)` or `error(...)`; both call `json.dumps` | MATCH |
| Never `raise` | No `raise` in any public handler; body wrapped in `except Exception` | MATCH |
| Errors `{"error": "..."}` | `runtime.error(message)` → `{"error": message}` | MATCH |
| `task_id = kwargs.get("task_id")` | Retrieval four call `kwargs.get("task_id")` and discard. Plan/evidence/citation/fanout do `del kwargs`. Nobody uses `task_id`. | DRIFT / minor vs spec §4.4 and facts §19 |
| Never return a dict | Confirmed | MATCH |

`runtime.dump` / `runtime.error` are the only serializers:

```84:89:agents/research-bot/plugins/hdr/runtime.py
def dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def error(message: str) -> str:
    return dump({"error": message})
```

Caveat (not a current break): `except Exception` does not catch `BaseException`. `json.dumps` failure inside `error()` after a failed dump is theoretically possible if a success payload is unserializable; the `except` then calls `error(str(exc))`, which is serializable. **MATCH** in practice.

### 1.5 Deterministic vs prompted (package rule)

Spec design rule: anything deterministic must not be prompted. Every handler in this plugin is **deterministic Python**. None call `ctx.llm`. Retrieval tools call `ctx.call_mcp` (Context7) or HTTP. That is host I/O, not a prompted tool. **MATCH.**

---

## 2. Inventory: spec §5.2 vs three live surfaces

Spec §5.2 names, in spec order, checked one-by-one against `plugin.yaml` `provides_tools`, `schemas.ALL`, and `_HANDLERS`.

| Spec §5.2 tool | Phase | `plugin.yaml` | `schemas.ALL` | `_HANDLERS` | Class |
| --- | --- | --- | --- | --- | --- |
| `research_plan` | 1 | yes | yes | `tools.plan.research_plan` | MATCH |
| `worker_brief` | 2,4 | yes | yes | `tools.fanout.worker_brief` | MATCH (name) |
| `worker_harvest` | 2,4 | yes | yes | `tools.fanout.worker_harvest` | MATCH (name) |
| `evidence_add` | 2,4 | yes | yes | `tools.evidence.evidence_add` | MATCH (name) |
| `evidence_search` | all | yes | yes | `tools.evidence.evidence_search` | MATCH (name) |
| `evidence_read` | all | yes | yes | `tools.evidence.evidence_read` | MATCH (name) |
| `evidence_stats` | 3 | yes | yes | `tools.evidence.evidence_stats` | MATCH (name) |
| `gap_scan` | 3 | yes | yes | `tools.plan.gap_scan` | MATCH (name) |
| `claim_verify` | 6 | yes | yes | `tools.citation.claim_verify` | MATCH (name) |
| `conflict_report` | 6 | yes | yes | `tools.citation.conflict_report` | MATCH (name) |
| `cite_source` | 6 | yes | yes | `tools.citation.cite_source` | MATCH (name; v2, not removed) |
| `scholar_search` | 2,4 | yes | yes | `tools.retrieval.scholar_search` | MATCH (name) |
| `archive_lookup` | 9 | yes | yes | `tools.retrieval.archive_lookup` | MATCH (name) |
| `resolve_library` | 2 | yes | yes | `tools.retrieval.resolve_library` | MATCH (name) |
| `docs_query` | 2 | yes | yes | `tools.retrieval.docs_query` | MATCH (name) |

No live extras. No live omissions. **MATCH** on inventory membership.

### 2.1 Removed from v1 — spec §5.3

| v1 name | Spec fate | Live plugin | Class |
| --- | --- | --- | --- |
| `source_ledger_add` | → `evidence_add` | gone | MATCH |
| `source_ledger_list` | → `evidence_search` | gone | MATCH |
| `source_ledger_check` | **deleted, not renamed** | gone (zero hits under `plugins/hdr/`) | MATCH |

`cite_source` remains. `resolve_library` / `docs_query` remain as Context7 facades. **MATCH.**

Overlap algorithm of `source_ledger_check` is not present as a named tool. `store/spans.py` `verify_claim` is exact `str.find` plus an 8-word fallback (see §3.7). That fallback is **DRIFT** from “deleted, not renamed — the overlap algorithm is gone,” not a reintroduced v1 tool.

---

## 3. Per-tool audit

For each tool: spec when-to-call, spec schema, live schema, live return, deterministic vs prompted, error envelope, can it raise.

JSON Schema in `schemas.py` is what the model sees. Handlers do **not** re-validate enums; they coerce with `str(...)` / `int(...)` and ignore unknown keys.

---

### 3.1 `research_plan`

**When to call (spec §5.2):** Phase 1. “Create/update the run: question decomposition, open questions, tier, budget. Returns the plan and the budget envelope.”  
Schema description: “at the start of a research job, or to update/status the run. Writes `run.json`. Deterministic budget envelope. Not a prompt.”

**Spec §5.4 (quote):**

```python
# research_plan
{"action": {"enum": ["create","update","status"]},
 "question": "str",
 "tier": {"enum": ["quick","standard","deep","exhaustive"], "default": "standard"},
 "open_questions": ["str"],          # each must be independently answerable
 "falsifiers": ["str"],              # what would prove the working answer wrong
 "constraints": {"since": "YYYY-MM-DD", "domains": ["…"], "exclude": ["…"]}}
# → {"run_id","tier","budget":{"tokens","fetches","seconds"},"open_questions":[…],"phase"}
```

**Live schema (`schemas.RESEARCH_PLAN`):** `action`, `question`, `tier`, `open_questions`, `falsifiers`, `constraints`. `required: []`. **No `enum` on `action` or `tier`.** `constraints` is a free `object`, not `{since, domains, exclude}`. **DRIFT / major** — the model can send `action: "foo"` or `tier: "max"`; create then uses `tier or "standard"` and only applies budget if `tier in TIERS`.

**Live handler (`tools/plan.py`):**

- Default `action` = `"create"`.
- `status`: `run.load_run()`; if missing → `{"error":"no active run"}`; else `{"ok": true, **current}` — the **entire** `run.json` (spend, children, governor, named_gaps, …). Spec return is the five-field envelope. **DRIFT / EXTRA / major** (`status` leaks and does not match §5.4).
- `update`: load or `empty_run()`.
- else (`create` or unknown action): `empty_run(question, tier or "standard")`. Unknown action is treated as create. **DRIFT / minor.**
- Overlay: question, tier (only if in `TIERS`, then copies `TIER_BUDGET`), open_questions, falsifiers, constraints (stored as the raw dict).
- Writes `governor` via `run.governor_state`, `save_run`.
- Success (create/update):

```json
{
  "ok": true,
  "run_id": "r-xxxxxx",
  "tier": "standard",
  "budget": {"tokens": 200000, "fetches": 25, "seconds": 360, "workers": 3},
  "open_questions": [],
  "phase": "plan",
  "governor": "GREEN"
}
```

Spec budget is `{tokens, fetches, seconds}`. Live adds `workers`. Success adds `ok` and `governor`. **EXTRA / minor** on those keys; implementers of the envelope should keep `ok` (facts error shape is complementary) but treat `workers` and `governor` as extras vs §5.4.

**`plugins.entries.hdr.settings.default_tier`:** `empty_run` uses `setting("default_tier", "standard")` only when the passed tier is **not** in `TIERS`. The create path passes `tier or "standard"`, so a missing tier never reads the plugin setting. **GAP / minor.**

**Does not write `todo`.** Spec §3.1: “PLAN: research_plan writes run.json + todo.” Handler only writes `run.json`. **GAP / minor** (todo is a first-party intercepted tool; the handler would need to call it or the skill must). Do not invent a Hermes todo API if the host does not expose one to plugins — **UNPROVEN**. If there is no plugin API for todo, this is a skill duty, not a tool duty; document that in the spec.

**Deterministic:** yes. **Raises:** no. **Error envelope:** `{"error": "..."}`.

| Item | Class | Sev |
| --- | --- | --- |
| Inventory / writes run.json / budget from `TIER_BUDGET` | MATCH | — |
| Schema enums + constraints shape | DRIFT | major |
| `status` returns full run | DRIFT | major |
| Extra `ok` / `governor` / `budget.workers` | EXTRA | minor |
| `default_tier` unused on create | GAP | minor |
| Does not write todo | GAP or docs | minor |
| Unused `task_id` | DRIFT | minor |

---

### 3.2 `gap_scan`

**When to call (spec §5.2):** Phase 3. “Open questions with < 2 independent sources, claims with only tier-C/D support, contradictions, stale sources. Returns the saturation number.”  
§3.6: “`gap_scan` computes and returns this number; the model does not estimate it.”  
Saturation rule: stop breadth when the last batch produced **< 20% new tier-A/B sources** **and** every open question has ≥ 2 independent supporting sources, or Governor is AMBER.

**Spec §5.4 (quote):**

```python
# gap_scan
{"detail": {"enum": ["summary","full"], "default": "summary"}}
# → {"saturation":0.14,"unanswered":[…],"thin":[…],"conflicts":[…],
#    "stale":[…],"recommend":"depth|synthesize|stop","new_source_yield":0.18}
```

**Live schema:** `detail` string, no enum, `required: []`. **DRIFT / minor.**

**Live return:**

```json
{
  "ok": true,
  "saturation": 0.0,
  "unanswered": [],
  "thin": [{"src":"S1","tier":"C","title":"…"}],
  "conflicts": [],
  "stale": [{"src":"S2","published": null}],
  "recommend": "synthesize",
  "new_source_yield": 0.0,
  "sources": 3
}
```

`thin` is capped at 5 unless `detail == "full"` (then 12). Extra key `sources`. Extra `ok`. **EXTRA / minor.**

**Live algorithm (this is the important gap):**

1. `saturation = new_source_yield = (count of last_batch_ids whose source.tier ∈ {A,B}) / max(1, len(last_batch_ids))`.  
   Spec wants **new** A/B sources in the last batch as a fraction of that batch. Live does not test “new vs already in ledger.” `prior = max(1, len(sources) - len(last_ids))` is computed and **never used**.  
   `last_batch_ids` is written by `worker_harvest` as “ids not in the previous `last_batch_ids`,” then **replaced** with only that delta. After harvest N+2, ids from harvest N fall out of `last_batch_ids` and are counted as new again. Dual-use of one field. **DRIFT / blocker** for the stopping rule.

2. **Unanswered:** for each `open_question`, a source “supports” it if  
   `question.lower()[:24] in title` OR `in quote` OR **`src.tier in {A,B}`**.  
   The third clause means **any single A/B source marks every open question answered.** A run with one arXiv card and five unanswered mandates reports `unanswered: []`. Unit test `test_plan_digest_and_gap_scan` plants a title that equals the question, so it does not catch this. **DRIFT / blocker.**

3. **Thin:** every source with tier C/D (not “claims with only C/D support”). **DRIFT / major.**

4. **Conflicts:** `claims.conflicts()` — contested nodes only. The claim graph is never written by any tool (see §3.8). Live conflicts are `[]` unless tests/evals call `upsert_claim`. **GAP / blocker** for the claim-graph half of gap_scan.

5. **Stale:** sources with `needs_backfill` (not recency/`since`). **DRIFT / major.**

6. **Recommend:** default `synthesize`; `depth` only if `unanswered` and governor GREEN/None; AMBER/RED → `synthesize`; HARD → `stop`. Combined with (2), recommend is almost always `synthesize`. **DRIFT / blocker** for phase 3 → 4.

Does write `run.json` fields `saturation`, `new_source_yield`, `named_gaps`, `phase="gap"`. Useful side effect. **MATCH** as persistence; values are wrong.

**Deterministic:** yes (and must stay so). **Raises:** no. **Errors:** `{"error": ...}` only on unexpected exceptions.

| Item | Class | Sev |
| --- | --- | --- |
| Returns the named §5.4 keys | MATCH | — |
| Saturation is a real float | MATCH vs P5 “returns a real saturation number”; **DRIFT** vs §3.6 definition | blocker |
| Unanswered / independent-source test | DRIFT | blocker |
| `last_batch_ids` semantics | DRIFT | blocker |
| Thin / stale definitions | DRIFT | major |
| Conflicts empty without writers | GAP | blocker |
| `detail` enum missing; extra `ok`/`sources` | DRIFT / EXTRA | minor |

---

### 3.3 `evidence_add`

**When to call (spec §5.2):** Phase 2,4. Manual register for PDFs, files, terminal-fetched data. Intake hook usually does this.

**Spec schema:** not in §5.4. Live: required `url`; optional `title`, `text`, `quote`, `kind`, `origin`.

**Live behavior:** canonicalize URL; `extract.extract_metadata(text, url)`; overlay title; `score.score_source`; if `text` then `bus.write_corpus` + `spans.select_spans`; `ledger.add_source(...)`. Empty `url` → `{"error":"url is required"}`.

**Live success return** is whatever `ledger.add_source` returns, dumped as JSON — **not** an Evidence Card:

```json
{
  "ok": true,
  "updated": false,
  "source": {
    "id": "S1",
    "run_id": "r-…",
    "url": "…",
    "canonical_url": "…",
    "archived_url": null,
    "title": "…",
    "authors": [],
    "publisher": "",
    "published": null,
    "retrieved": "2026-08-27T…",
    "doi": null,
    "arxiv": null,
    "kind": "…",
    "tier": "A",
    "tier_reason": "…",
    "corpus": "corpus/<sha>.txt",
    "bytes": 123,
    "content_hash": "sha256:…",
    "spans": [{"q":"…","off":0,"len":n}],
    "claims": [],
    "origin": "manual",
    "fetch_status": "ok",
    "duplicate_of": null,
    "needs_backfill": false,
    "quote": "…"
  }
}
```

Dedupe path sets `"updated": true` and returns the existing row (fills empty fields only). **MATCH** to “canonicalizes and stores corpus.” Return shape is unspecified in §5.4 — **UNPROVEN** vs a card; treat the full source row as acceptable unless a later audit of the bus card format requires alignment.

Does **not** call `claims.upsert_claim`. `source.claims` stays `[]`.

Missing `text` → `needs_backfill: true`, no corpus. **MATCH** to backfill story.

**Deterministic:** yes. **Raises:** no.

| Item | Class | Sev |
| --- | --- | --- |
| Manual add + canonicalize + metadata + spans | MATCH | — |
| Return is ledger row, not card | UNPROVEN / EXTRA vs §3.2 card | docs |
| No claim-graph write | GAP (shared) | blocker |

---

### 3.4 `evidence_search`

**When to call:** any phase. “Query the ledger/corpus (BM25-ish over titles, spans, claims). Returns cards, never full text.”  
§5.3: this **replaces dump-style** `source_ledger_list`.

**Live schema:** optional `query`. Empty query is legal.

**Live behavior:**

1. If `query` nonempty: `store.index.search(query, limit=25)` (Okapi-ish BM25 over title/quote/publisher/authors/span.q/claim strings). If ranked hits, map ids back to sources. If the index is empty, fall back to `ledger.list_sources(query=query)` (substring over id/url/title/quote/kind/publisher).
2. If `query` empty: first 25 sources in ledger order — a **dump**. **DRIFT / major** vs “query, not dump.”

**Live return:**

```json
{
  "ok": true,
  "count": 1,
  "backfill_needed": 0,
  "cards": [
    {
      "id": "S1",
      "title": "…",
      "url": "https://…",
      "tier": "A",
      "kind": "primary",
      "spans": [{"q":"…","off":0,"len":n}],
      "needs_backfill": false
    }
  ]
}
```

No full text. **MATCH** on “never full text.” `backfill_needed` supports §6.2. Cards are thinner than the §3.2 intake card (no publisher/published/full/read_more). **DRIFT / minor.**

Index is not updated for sources added only via harvest URL stubs until `add_source` runs (it does call `index.update_source`). Corpus body text is **not** indexed — only titles/spans/claims. Spec says “ledger/corpus.” **DRIFT / minor.**

**Deterministic:** yes. **Raises:** no.

---

### 3.5 `evidence_read`

**When to call:** only when a card span is not enough. “The only sanctioned way to pull raw text back into the window.”

**Spec §5.4 (quote):**

```python
# evidence_read
{"src": "S17", "offset": 48000, "limit": 4000, "around_span": 2}   # chars
```

No spec return shape.

**Live schema:** required `src`; optional `offset`, `limit`, `around_span`. **MATCH** on inputs. Comment in spec says chars; `bus.read_corpus` slices a Python `str` (Unicode code points), not bytes. Filenames are content-addressed text. **DRIFT / minor** if a later fixer treats `off` as bytes (spans store `off` from `str.find` on the same text, so they are consistent with each other).

**Live behavior:** `ledger.get_source(src)` → `{"error":"unknown source S…"}`; no corpus → `{"error":"S… has no corpus (needs_backfill or pruned)"}`. Digest = last path component minus `.txt`. If `around_span` is set and spans exist, `offset = max(0, span.off - 200)` (limit unchanged). Then `dump(bus.read_corpus(...))`.

**Live success return (`bus.read_corpus`):**

```json
{"ok": true, "sha256": "<digest>", "offset": 48000, "limit": 4000, "total": 41209, "text": "…"}
```

Missing file: `{"error":"corpus file missing: <digest>"}` (not wrapped by `runtime.error`, still the official error key). **MATCH.**

Default `limit` 4000. Reads the **entire** file into memory, then slices. Large PDFs can spike RSS. **EXTRA / minor** (implementation risk, not a schema break).

**Deterministic:** yes. **Raises:** no (`int("x")` is caught).

---

### 3.6 `evidence_stats`

**When to call (spec §5.2):** Phase 3. “Coverage numbers: sources by tier, **per-open-question support counts**, new-source yield of the last batch.”

**Live schema:** empty object. **MATCH** (no args).

**Live return:**

```json
{
  "ok": true,
  "sources": 4,
  "by_tier": {"A": 1, "B": 0, "C": 2, "D": 1},
  "open_questions": ["…"],
  "new_source_yield": null,
  "governor": "GREEN"
}
```

`open_questions` is the **list of question strings**, not per-question support counts. `new_source_yield` is whatever `gap_scan` last wrote (or `null`). Extra `governor`. **GAP / major** on per-question counts. **EXTRA / minor** on `governor`.

**Deterministic:** yes. **Raises:** no.

---

### 3.7 `claim_verify`

**When to call:** Phase 6, before asserting a fact. Exact-span provenance. Not lexical overlap.  
§3.4: `source_ledger_check` dies; replacement is exact substring + numeric digits + entity check. Unsupported claim → Citation Gate (hook, out of scope).

**Spec §5.4 (quote):**

```python
# claim_verify
{"claim": "str", "candidate_sources": ["S17","S22"]}   # optional; defaults to all
# → {"status":"supported","evidence":[{"src":"S17","off":48213,"len":137,
#     "exact":true,"numeric_match":true,"span":"…"}],"unsupported_parts":[…]}
```

**Live schema:** required `claim`; optional `candidate_sources` string array. **MATCH.**

**Live return:**

```json
{
  "ok": true,
  "status": "supported|partial|unsupported",
  "evidence": [
    {
      "src": "S1",
      "off": 0,
      "len": 54,
      "exact": true,
      "numeric_match": true,
      "entity_match": true,
      "span": "…"
    }
  ],
  "unsupported_parts": []
}
```

`entity_match` is in §3.4 prose but not in the §5.4 example object. **EXTRA / minor** on the key; **MATCH** to §3.4.

**Live algorithm (`store/spans.py` `verify_claim`):**

1. `text.find(claim)` — exact whole-claim substring. **MATCH.**
2. If miss: search contiguous **8–12 word** chunks of the claim; if one hits, set `exact=True` and `span` to that chunk. **DRIFT / major.** This is not lexical-overlap scoring, but it is not “the claim is an exact span.” A long paraphrase that shares an 8-word clause can become `supported`. This is the closest living relative of deleted `source_ledger_check`.
3. `numeric_match`: claim digits ⊆ span digits (or no digits in claim). **MATCH.**
4. `entity_match`: capitalized tokens from the claim appear in the span (or nearby 200 chars). **MATCH** to §3.4.
5. Handler `status`: `unsupported` if no evidence; `supported` only if **every** evidence row has both numeric and entity match; else `partial`. A single sloppy source can keep the claim out of `supported` even if another source is clean. **DRIFT / minor.**
6. `unsupported_parts` is either `[claim]` or `[]` — never a segmentation of the claim. **DRIFT / minor.**
7. Does **not** `upsert_claim`. Verification is stateless vs the claim graph. **GAP / blocker** (shared with §3.8).
8. Reads up to 2_000_000 chars of every candidate corpus into the handler. **EXTRA / minor** (perf).

Sources without corpus are skipped (no error). Empty claim → `{"error":"claim is required"}`.

**Deterministic:** yes (required). **Raises:** no.

Unit test `test_claim_verify_and_conflicts` uses the **entire page text as the claim**, so `find` hits. It does not test the 8-word fallback or a true paraphrase.

---

### 3.8 `conflict_report`

**When to call:** Phase 6. “Every claim where sources disagree. Do not average.”  
§3.5: emit where **tier-A sources disagree**, or newest vs most-cited.

**Live schema:** empty. **MATCH.**

**Live return:**

```json
{"ok": true, "count": 0, "conflicts": []}
```

`conflicts()` returns nodes with `status == "contested"` (`supports` and `contradicts` both present). It does **not** filter to tier-A, does **not** compare newest vs most-cited, does **not** attach source tiers. **DRIFT / major** vs §3.5.

**Writer gap:** `store.claims.upsert_claim` is the only writer. Callers in-repo: `tests/test_hdr_plugin.py`, `evals/run_offline.py`. **Zero** plugin tools or hooks call it. `claim_verify` does not. `cite_source` does not. Intake does not. In a real run, `claims.json` stays `{}` and this tool is a no-op. **GAP / blocker.**

**Deterministic:** yes. **Raises:** no.

---

### 3.9 `cite_source` (v2, stays)

**When to call:** after every factual claim, and before delivering a brief. “Use only this formatted text. Never invent bibliography entries.” Only sanctioned bibliography producer.

**Live schema:** optional `ids` (array of `S#`); optional `style` (`apa|ieee|chicago` in prose, not enum).

**Live behavior:** style from arg or `runtime.citation_style()` (`ctx.get_config("citation_style")`, default `apa`). If `ids` omitted, formats **every** ledger source (“omit to cite the run” — schema description). Missing ids listed in `missing_ids`. `_format` is string templates; no LLM.

**Live return:**

```json
{
  "ok": true,
  "style": "apa",
  "count": 1,
  "citations": [{"id":"S1","n":1,"text":"Author (2024). Title. Pub. https://…","url":"https://…"}],
  "missing_ids": []
}
```

**MATCH** as a deterministic formatter. IEEE/Chicago are heuristic, not CSL. **UNPROVEN** vs a style guide; good enough vs “never invent a row.” Unknown `style` falls through to APA-like. **DRIFT / minor** (no enum reject).

Used by `hooks/output.py` `transform_llm_output` (not a tool). That is the spec’s deterministic bibliography path.

**Raises:** no.

---

### 3.10 `worker_brief`

**When to call:** before `delegate_task`. Compile a self-contained child brief. Returns text to paste into goal/context.

**Spec §5.4 (quote):**

```python
# worker_brief
{"open_question": "str", "boundary": "str",   # what this worker must NOT cover
 "must_find": ["str"], "source_types": ["primary","filing","paper"],
 "max_fetches": 12, "return_format": "evidence_cards"}
```

**Live schema:** required `open_question`; optional `boundary`, `must_find`, `source_types`, `max_fetches`, `return_format`. **MATCH** on fields. No enums on `source_types` / `return_format`. **DRIFT / minor.**

**Live success:**

```json
{"ok": true, "brief": "GOAL:\n…\nBOUNDARY:\n…", "goal": "<open_question>", "max_fetches": 12}
```

`brief` is a single string with GOAL / BOUNDARY / siblings / METHOD / OUTPUT CONTRACT (FINDING / CARDS / GAPS / CONFIDENCE). Defaults: `source_types=["primary"]`, `max_fetches=12`, `return_format=evidence_cards`, boundary auto-filled from sibling `open_questions` if omitted.

**§7.2 four parts:** Goal, Boundary, Method, Output contract. Live includes all four headings. Method is missing **recency constraint** from `run.constraints.since`. `must_find` is accepted and **not interpolated into the brief**. **GAP / major** (`must_find` is dead). Recency **GAP / minor.**

**Governor (EXTRA vs schema, MATCH vs §3.3 intent):**

- RED/HARD → `{"error":"governor RED: refuse new worker brief. Synthesize from the ledger."}`
- AMBER → refuse unless `open_question` fuzzy-matches `named_gaps` or `open_questions`

This is deterministic policy in the tool, not only in `pre_tool_call`. Fine; keep it. **EXTRA / minor** vs §5.4, **MATCH** vs governor.

Writes `run.children[question] = {status: briefed, max_fetches, boundary}`. Keyed by question text, while `worker_harvest` keys children by `subagent_id`. **DRIFT / minor** (orphan maps).

**Deterministic:** yes. **Raises:** no.

---

### 3.11 `worker_harvest`

**When to call:** after a child finishes. Counts and ids only. Zero raw page text.

**Live schema:** optional `subagent_id`, `transcript_path`.

**Live return:**

```json
{
  "ok": true,
  "new_ids": ["S1","S2"],
  "count": 2,
  "transcript_ids": ["S1"],
  "transcript_urls": 1,
  "finding_chars": 42
}
```

No finding text, no page body. **MATCH** to “zero raw page text.” `transcript_ids` is a list of `S#` (more than “counts”). **EXTRA / minor.**

**Live behavior:**

1. `new_ids` = ledger sources for this `run_id` whose id is **not** in `run.last_batch_ids`. First harvest therefore reports **every** source on the run as new, including parent-added cards. **DRIFT / major.**
2. Then overwrites `last_batch_ids` with that delta (see §3.2). **DRIFT / blocker** shared with `gap_scan`.
3. Transcript: explicit path or `_default_transcript(subagent_id)` under `$HERMES_HOME/cache/delegation/live/**/task-*.log` (facts §11 path). Grep URLs and `S#` and `FINDING:` in **this process**. Spec §7.3 says “greps those with `execute_code`.” Same result, different surface — **DRIFT / docs** (do not invent an execute_code requirement if in-process grep is cheaper and deterministic).
4. For each transcript URL with no corpus, `ledger.add_source(..., needs_backfill=True)`. Side effect. **MATCH** to backstop.
5. `_default_transcript` reads the first 2000 chars of every `task-*.log` looking for `subagent_id`. Can be slow; still in the `try`.

**Deterministic:** yes. **Raises:** no.

---

### 3.12 `resolve_library`

**When to call:** user named a library; need Context7 id. Facade over MCP. Must return an openable docs URL or the result does not enter the ledger. Do not call raw `mcp_*`.

**Live schema:** required `query`; optional `library_name`. Official Context7 `resolve-library-id` wants both `query` and `libraryName` (Context7 MCP, this session). Live sends `libraryName` only if provided. **DRIFT / minor** vs the upstream MCP schema; **MATCH** vs spec §5.2 (query is enough for the facade).

**Live behavior:** `runtime.call_mcp("context7", "resolve-library-id", payload)` → `normalize_envelope` → `first_openable_url` on the JSON blob. If a `http(s)` URL is found, `ledger.add_source` with `origin=mcp:context7`, `tier=A`, `needs_backfill=True`, `quote=blob[:400]`. Then:

```json
{ "...envelope", "openable_url": "https://…"|null, "ledger": true|false }
```

If MCP is missing: envelope `{ok: false, error: "ctx.call_mcp is not available…"}`, `ledger: false`. Run continues. **MATCH** to spec §9 “facade returns a structured error.” Test `test_docs_query_requires_openable_url` covers the sibling.

Does not invent OpenAlex/PubMed MCP. **MATCH** facts STOP.

**Deterministic** (host I/O). **Raises:** no. `kwargs.get("task_id")` called, unused.

---

### 3.13 `docs_query`

**When to call:** have a library id; need docs text. Same openable-URL / no raw `mcp_*` rules.

**Live schema:** required `library_id`, `query`; optional `tokens`. **MATCH.**

**Live:** `call_mcp("context7", "query-docs", {libraryId, query, tokens?})`. Same URL/ledger rule as resolve. **MATCH.**

May dump a large MCP envelope into the model-visible JSON (`{**envelope, openable_url, ledger}`). Spec wants the bus to card retrieval results via `transform_tool_result` (hook audit). If the hook lists `docs_query`, the handler’s fat envelope may still hit the model before/instead of a card — **UNPROVEN** here; flag for the hooks auditor.

**Raises:** no.

---

### 3.14 `scholar_search`

**When to call:** academic sweep. Spec §5.2: “via MCP or HTTP fallback. Returns cards with DOI + OA link.”  
Facts STOP: `openalex` / `pubmed` are **not** first-party Hermes MCP servers. Facades use HTTP (Crossref, Unpaywall, Wayback CDX). Do not invent official MCP URLs.

**Live schema:** required `query`; optional `limit`. Description says “Crossref / OpenAlex-style.” No OpenAlex HTTP. **DRIFT / docs** on the description.

**Live behavior:** GET `https://api.crossref.org/works?query&rows` with `CROSSREF_MAILTO` or `UNPAYWALL_EMAIL` as `mailto`. On HTTP/JSON failure: `{"ok": false, "error": "crossref unavailable: …", "cards": []}` — structured, run continues. **MATCH** facts. Unpaywall OA lookup only if `UNPAYWALL_EMAIL` is set. Each DOI → `https://doi.org/{doi}` → `ledger.add_source` (`origin=scholar`, `tier=A`, `needs_backfill=True`). Cards: `{id, title, doi, url, oa, publisher}`.

No MCP attempt (no invented server). Spec §5.2 “via MCP or HTTP” is **docs DRIFT**; live correctly follows facts. `SEMANTIC_SCHOLAR_API_KEY` is listed in spec §4.2 env and unused here. Do **not** invent a Semantic Scholar path unless a later spec says so. **docs.**

Limit clamped 1–20 for Crossref `rows`, then sliced to `limit`. **MATCH** enough.

**Deterministic** HTTP. **Raises:** no.

---

### 3.15 `archive_lookup`

**When to call:** dead or changed URL. Spec: “Wayback/Memento HTTP. Stores `archived_url`.”

**Live schema:** required `url`. **MATCH.**

**Live:** Wayback CDX `web.archive.org/cdx/search/cdx` (`output=json`, `limit=1`, `statuscode:200`). Success: `{"ok": true, "url", "archived_url": "https://web.archive.org/web/{ts}/{url}", "timestamp"}` and `ledger.add_source` with `archived_url`, `fetch_status=archived`, `needs_backfill=True`. Failures: `ok: false` + error (`wayback unavailable`, `no archived snapshot`, `malformed cdx`).

**No Memento** (`Accept-Datetime` / TimeMap). **GAP / minor** vs the word “Memento”; **MATCH** vs facts (Wayback CDX is the named official-fallback HTTP). Prefer facts: do not invent a Memento server. If Memento is wanted, it is more HTTP, not an MCP server.

**Deterministic** HTTP. **Raises:** no.

---

## 4. Cross-cutting findings

### 4.1 Schema quality (model-facing)

`schemas.py` descriptions include “When to call” (official plugins page: descriptions must tell the model when to call). **MATCH.**

Almost no JSON Schema `enum`s, despite §5.4 listing them for `research_plan.action`, `research_plan.tier`, `gap_scan.detail`. **DRIFT / major** as a group.

`required` arrays: `evidence_add`/`claim_verify`/`worker_brief`/`resolve_library`/`docs_query`/`scholar_search`/`archive_lookup`/`evidence_read` match handler checks. `research_plan` has no required fields — create with `{}` writes an empty-question run. **DRIFT / minor.**

### 4.2 Error envelope consistency

| Pattern | Tools |
| --- | --- |
| `runtime.error` only | plan, evidence, citation, fanout validation |
| `{ok:false, error, cards:[]}` | `scholar_search` Crossref down |
| `{ok:false, error}` | `archive_lookup` CDX down / empty |
| MCP envelope + `openable_url`/`ledger` | resolve / docs |
| Store `{error}` dumped as-is | `evidence_read` missing corpus file |

Official: errors are `{"error":"..."}`. The HTTP tools add `ok: false` and sometimes extra keys. **DRIFT / minor.** A fixer should pick one envelope and use it everywhere. Do not invent a Hermes envelope beyond `{error}` / `{ok, result}`.

### 4.3 Claim graph is disconnected from tools

§3.5 / §6.1: every ledger entry links to claim nodes; graph is “built as a side effect of the citation pass.”  
Live: `upsert_claim` exists; no tool calls it; `conflict_report` and `gap_scan.conflicts` read it. **GAP / blocker.**

Fix direction (do not apply here): `claim_verify` should upsert each (claim, src, stance) when `exact` is true (`supports`) or false after a candidate was given (`silent` / leave unsupported). Do not prompt a stance.

### 4.4 Budget table

`runtime.TIER_BUDGET` matches spec §3.6 (quick 40k/5/90/0, standard 200k/25/360/3, deep 800k/80/1200/6, exhaustive 3M/250/3600/10). **MATCH.** `research_plan` is the only tool that writes it onto `run.json`.

### 4.5 `config.yaml` (this slice only)

```yaml
custom_toolsets:
  research:
    - web
    - browser
    - vision
    - file
    - terminal
    - code_execution
    - skills
    - memory
    - session_search
    - todo
    - clarify
    - delegation
    - cronjob
    - hdr
toolsets:
  - research
plugins:
  enabled:
    - hdr
```

**MATCH** facts STOP (no `moa` toolset, no `army`, no `research-bot` toolset). Spec §4.2 still lists `moa` and a wider `mcp_allowlist` — **docs** for the spec maintainer, not this plugin.

### 4.6 Official STOPs (not defects)

1. No `moa` toolset. Live complies.
2. No first-party `openalex` / `pubmed` / `wayback` MCP. Live HTTP facades comply.
3. Path install only — out of this slice.
4. No `hermes plugins doctor` — out of this slice.
5. Never reintroduce `army-runtime` or toolset `research-bot`. Live complies.

### 4.7 What was not proven

- Live Hermes 0.19.0 `ctx.register_tool` / `ctx.call_mcp` signatures on a real host.
- Children resolving the same `plugin-data/hdr` (`HERMES_HOME` `[INF]` in spec §7.3 / facts §UNV).
- Whether `transform_tool_result` cards `docs_query` / `scholar_search` results so the handler envelope is not what the model sees.
- Whether a plugin can write the first-party `todo` tool from `research_plan`.

---

## 5. Long status table

| Tool | When-to-call vs spec | Schema vs §5.4 | Return vs spec | Det. | Error | Raises | Class | Sev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `research_plan` | MATCH | DRIFT (no enums) | DRIFT (`status` full run; extra keys) | yes | `{error}` | no | DRIFT | major |
| `gap_scan` | MATCH | DRIFT (no enum) | keys MATCH; numbers DRIFT | yes | `{error}` | no | DRIFT | blocker |
| `evidence_add` | MATCH | n/a §5.4 | ledger row (UNPROVEN vs card) | yes | `{error}` | no | MATCH | — |
| `evidence_search` | MATCH | optional query | cards MATCH; empty=dump DRIFT | yes | `{error}` | no | DRIFT | major |
| `evidence_read` | MATCH | MATCH | `{ok,sha256,offset,limit,total,text}` | yes | `{error}` | no | MATCH | — |
| `evidence_stats` | MATCH | MATCH | GAP per-question counts | yes | `{error}` | no | GAP | major |
| `claim_verify` | MATCH | MATCH | extra `entity_match`/`ok`; 8-word exact | yes | `{error}` | no | DRIFT | major |
| `conflict_report` | MATCH | MATCH | empty graph; no tier-A rule | yes | `{error}` | no | GAP | blocker |
| `cite_source` | MATCH | no style enum | citations[] MATCH | yes | `{error}` | no | MATCH | — |
| `worker_brief` | MATCH | MATCH fields | `{ok,brief,goal,max_fetches}`; `must_find` unused | yes | `{error}` | no | DRIFT | major |
| `worker_harvest` | MATCH | MATCH | counts+ids; `last_batch_ids` DRIFT | yes | `{error}` | no | DRIFT | blocker |
| `resolve_library` | MATCH | MATCH | envelope+url+ledger | yes | `{error}` / MCP | no | MATCH | — |
| `docs_query` | MATCH | MATCH | same | yes | `{error}` / MCP | no | MATCH | — |
| `scholar_search` | MATCH (facts) | MATCH | cards+DOI+OA | yes | `{ok:false,error,cards}` | no | MATCH | — |
| `archive_lookup` | MATCH (facts) | MATCH | archived_url | yes | `{ok:false,error}` | no | MATCH | — |

**Removed v1 tools:** MATCH (gone).  
**Toolset `hdr`:** MATCH.  
**`register` covers every schema:** MATCH.  
**Handlers JSON / `**kwargs` / no raise:** MATCH.  
**`task_id` used:** DRIFT (minor).

---

## 6. Numbered fix list (do not apply)

Implement in this order. Each item is scoped so it can be a single PR. Do not invent Hermes knobs. Do not add MCP servers named `openalex` / `pubmed` / `wayback`. Do not add toolset `moa`, `research-bot`, or `army`.

1. **[blocker] Wire the claim graph.** In `claim_verify`, after scoring, call `claims.upsert_claim(claim, src=…, stance=supports|silent, span=off)` for each candidate that was examined. Stance is deterministic from `exact`. Without this, `conflict_report` and `gap_scan["conflicts"]` stay empty in production.

2. **[blocker] Fix `gap_scan` unanswered.** A source supports an open question only if its spans/title/quote actually mention that question (or a stored claim node links them). **Delete** the clause `or src.get("tier") in {"A","B"}`. Require ≥ 2 distinct `canonical_url`s.

3. **[blocker] Split `last_batch_ids` from “seen ids.”** `run.json` should keep `seen_ids` (monotonic) and `last_batch_ids` (this harvest only). `worker_harvest` computes `new_ids = current_ids - seen_ids`, then `last_batch_ids = new_ids`, `seen_ids |= new_ids`. `gap_scan` yield = (new ids whose tier is A/B) / max(1, len(last_batch_ids)). Remove the unused `prior` local.

4. **[blocker] Make `saturation` and `recommend` match §3.6.** `new_source_yield` as in (3). `saturation` should encode both yield **and** “every open question has ≥ 2 independent supports” (do not make the model compute it). `recommend`: `depth` if unanswered and governor GREEN; `synthesize` if yield < 0.20 and unanswered is empty, or governor AMBER/RED; `stop` if HARD.

5. **[major] Tighten `claim_verify` exactness.** `exact=True` only when `claim` (stripped) is a contiguous substring of the corpus. Keep the 8-word walk as a **separate** `partial_span` field if you want a hint; do not set `status=supported` from it. That is how `source_ledger_check` stays deleted.

6. **[major] Add §5.4 enums to live schemas.** `research_plan.action` `["create","update","status"]`; `tier` `["quick","standard","deep","exhaustive"]`; `gap_scan.detail` `["summary","full"]`; `cite_source.style` `["apa","ieee","chicago"]`. Handlers should reject unknown enums with `{"error":"…"}` instead of coercing.

7. **[major] `research_plan` `status` return.** Return the §5.4 envelope (`run_id`, `tier`, `budget` `{tokens,fetches,seconds}`, `open_questions`, `phase`), plus `ok`. Do not splat `**current`.

8. **[major] `evidence_stats` per-question counts.** e.g. `by_question: [{"q":"…","support":2,"tiers":{"A":1,"B":1}}]`. Reuse the same support rule as fix (2).

9. **[major] `evidence_search` empty query.** Do not dump the ledger. Require `query` or return `{"error":"query is required"}` (this is the point of deleting `source_ledger_list`).

10. **[major] Interpolate `must_find` (and `constraints.since`) into `worker_brief`.** Dead args are a schema lie.

11. **[major] `conflict_report` §3.5 filter.** After (1), emit rows where tier-A stances disagree, or newest contradicts most-cited. Include `src`, `stance`, `tier` on each support edge. Do not average.

12. **[major] Align `gap_scan` thin/stale.** Thin = open questions / claims whose **only** support is C/D, not “every C/D source.” Stale = `published` before `constraints.since`, or `needs_backfill` listed under a different key (`backfill`), not as `stale`.

13. **[minor] Use `default_tier` on create** when `args.tier` is omitted (`setting("default_tier","standard")`).

14. **[minor] `task_id = kwargs.get("task_id")`** in every handler (even if unused) to match spec §4.4 / facts §19. Do not key store files on it unless a host probe shows isolation requires it (**UNPROVEN**).

15. **[minor] One error envelope.** Prefer `{"error":"..."}` for all failures. If `ok: false` is kept on HTTP tools, keep `error` too (already true).

16. **[minor] `research_plan` todo.** If the host exposes no plugin API for the intercepted `todo` tool, do **not** invent one. Update spec §3.1 to say the skill writes todos. If `ctx` can call todo, write the open questions there. **UNPROVEN** — probe first.

17. **[minor] `worker_brief` / `worker_harvest` child keys.** Use `subagent_id` or a brief id on both sides so `run.children` is one map.

18. **[minor] `resolve_library`:** if `library_name` is omitted, pass `libraryName=query` so Context7’s required field is filled. Still no invented MCP.

19. **[docs] Spec vs facts.** Spec §4.2 still lists toolset `moa` and MCP `openalex`/`pubmed`/`wayback`. Facts STOP says remove them. Live `config.yaml` already follows facts. Edit the spec; do not “fix” the plugin back to §4.2.

20. **[docs] Spec §5.2 `scholar_search` “via MCP or HTTP.”** Change to “HTTP Crossref + optional Unpaywall” to match facts and live code.

21. **[docs] Schema description “OpenAlex-style.”** Remove or retitle to Crossref. Do not add an OpenAlex client unless spec+facts agree.

22. **[docs] Memento.** Either drop the word from spec §5.2 / schema description or add a second HTTP TimeGate call. Not an MCP server.

23. **[docs] `evidence_add` / `evidence_read` return shapes.** Add them to §5.4 so the next implementer does not guess. Current live shapes are recorded in §3.3 and §3.5.

24. **[docs / extra] Drop or document extras:** `budget.workers`, `governor` on plan/stats, `gap_scan.sources`, `entity_match`, harvest `transcript_ids`. Prefer documenting them in §5.4 over deleting if hooks already consume them.

25. **Do not do:** reintroduce `source_ledger_*`; rename `claim_verify` back; add toolset `moa`; add `army-runtime`; register tools on toolset `research-bot`; add `plugin.json`; call raw `mcp_*` from skills; invent `hermes plugins doctor`.

---

## 7. Files a fixer will touch

| Fix | File |
| --- | --- |
| 1, 5 | `plugins/hdr/tools/citation.py`, `plugins/hdr/store/spans.py`, `plugins/hdr/store/claims.py` |
| 2, 3, 4, 12 | `plugins/hdr/tools/plan.py`, `plugins/hdr/store/run.py`, `plugins/hdr/tools/fanout.py` |
| 6 | `plugins/hdr/schemas.py` + handler validation |
| 7, 13 | `plugins/hdr/tools/plan.py` |
| 8 | `plugins/hdr/tools/evidence.py` |
| 9 | `plugins/hdr/tools/evidence.py`, `plugins/hdr/schemas.py` |
| 10, 17 | `plugins/hdr/tools/fanout.py` |
| 11 | `plugins/hdr/store/claims.py`, `plugins/hdr/tools/citation.py` |
| 14 | all five `tools/*.py` |
| 18 | `plugins/hdr/tools/retrieval.py` |
| 19–24 | `docs/HDR-SPEC.md` / schema descriptions — **not this plugin’s behavior** |
| Tests to extend | `tests/test_hdr_plugin.py` (`test_plan_digest_and_gap_scan` currently cannot see fix 2; `test_claim_verify_and_conflicts` plants the graph by hand and uses the full page as the claim) |

---

## 8. Verdict

The **host package is correctly shaped**: native `plugin.yaml` + `register(ctx)`, toolset `hdr`, fifteen spec tools, three v1 ledger tools gone, handlers return JSON strings, accept `**kwargs`, and do not raise. `config.yaml` enables `hdr` and does not enable `moa` / `army` / `research-bot` as a toolset. Context7 stays a facade; scholar/archive are HTTP.

The **research loop is not correctly computed**. `gap_scan` will under-report unanswered questions as soon as any A/B source exists; `worker_harvest` / `last_batch_ids` corrupt the saturation input; `conflict_report` has no production writer. `claim_verify` is deterministic but weaker than “exact span” because of the 8-word fallback.

That is a plugin/tools problem, not a missing tool name. Fix the algorithms and the claim-graph write; do not add tools.
