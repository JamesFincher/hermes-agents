# Profile canvas: counsel-bot

## 1. Job
Drafts legal documents and retrieves primary US law under a practice hat, and
refuses to emit a citation or a concrete fact it did not retrieve. It does not
advise, file, appear, sign, or predict outcomes.

## 2. Who it beats
General-purpose chat models used for legal drafting, and the current generation
of AI legal assistants — on one axis: **fabrication rate**. The public failure
mode of AI in law is invented citations reaching filings. The bar is not
eloquence; it is refusal.

## 3. Mechanisms to reproduce (and where they land)
| Mechanism | Source of the idea | Hermes surface |
| --- | --- | --- |
| Retrieval-grounded assertion | RAG practice generally | `transform_tool_result` intake + authority ledger |
| Citation verification against a real corpus | CourtListener's citation-lookup API, built explicitly as a hallucination guardrail | `store/cites.py` + `pre_tool_call` gate |
| Required-elements contracts per document | practice checklists / form books | `data/doc_types.json` + `draft_scaffold` |
| Placeholder discipline | how human drafters actually work | fact fence in `store/gates.py` |
| Jurisdiction as the primary axis | black-letter reality of US law | `matter.json` + jurisdiction fence |
| Currency / as-of dating | statutory amendment risk | currency gate + `authority_status` |
| Parallel issue research, condensed returns | orchestrator-worker deep research | `worker_brief` + `delegate_task` |
| Separate verification pass | Claude Research's citation agent | `cite-check` skill + `draft_check` |
| Deterministic date math | nothing about deadlines should be inferred | `store/rules.py` |

## 4. The loop
intake → hat → facts → issue plan → parallel authority retrieval → read →
scaffold → draft → gates → write → deliver with placeholders, assumptions, and
what a reviewer must check first.

Network is touched only in the retrieval phase. Drafting reads the ledger only.

## 5. Scarce resource
**Trust.** One fabricated citation destroys the profile's value entirely,
regardless of how good everything else was. Tokens are second; correctness of
refusal is first. This is why gates fail closed on the write path.

## 6. Durable state
`plugin-data/lex/`: `ledger.json` (authorities, schema-versioned),
`corpus/<sha>.txt` (write-once full text), `matters/<id>.json` (jurisdiction,
hat, fact table, issue plan, budget), `audit/*.jsonl` (every gate decision).
Survives compaction, `/new`, and profile update.

## 7. Custom surface
Patterns used (playbook §4): **intercept-and-distil** (authority cards),
**fence** (dedupe + write gate + UPL), **free output** (disclaimer and citation
warning via `transform_llm_output`), **ledger** (authorities + matter facts).
Four of five. The Governor pattern is present in reduced form as budget
accounting without hard fences — deliberate: refusing a lawyer's tool mid-task
on cost grounds is worse than the cost.

15 tools, 12 hooks, 2 cache-safe prompt sections, 3 deterministic scripts.

## 8. Fan-out
Flat (`max_spawn_depth: 1`). One child per legal issue, cheap model, explicit
boundary, output contract of four blocks. Children register authorities into the
shared ledger; the parent harvests ids and counts. `subagent_stop` flags any
authority id a child claimed that is not actually in the ledger.

## 9. Knob sweep
Recorded inline in `config.yaml`. Notable: docker backend (untrusted PDFs +
matter facts), `memory.write_approval: true` (a wrong remembered fact is worse
than no memory), `proactive_prune_tokens: 48000`, `verify_on_stop: false`
because it never fires on markdown-only turns and our gate replaces it.

## 10. Failure ladder
CourtListener down → `fetch_authority.py` direct → web_extract, marked
unverified. No token → every citation reported unverified, never trusted.
eCFR MCP absent → documented public REST API via script. JS-only court portal →
browser toolset. Scanned PDF → vision. Dead link → report the gap; never
substitute a similar authority.

## 11. Eval
12 frozen tasks, 4 adversarial (fabrication bait, injection, "fill in the
blanks with standard values"). Deterministic gates in CI. Rubric floor: zero on
citation integrity or scope discipline fails regardless of the mean.

## 12. Honest limits
See `HONEST-LIMITS.md`. Headline: the gate proves a citation exists, not that it
supports the sentence. Local rules are the least accessible material in American
law. Matter data is stored in plaintext with no privilege protection.
