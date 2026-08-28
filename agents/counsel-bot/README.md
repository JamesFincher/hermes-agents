# counsel-bot

A Hermes profile that drafts legal documents and retrieves primary law, and
that **refuses to write a citation or a fact it did not retrieve**.

> **This is not a lawyer and does not give legal advice.** It is a drafting and
> research instrument whose output is work product for review by a licensed
> attorney, or by a self-represented person who understands they are
> representing themselves. It does not file, serve, appear, sign, or predict
> outcomes. See `HONEST-LIMITS.md` before using it for anything real.

---

## The one idea

Language models fabricate citations. They have done it in enough real filings to
produce a genre of sanctions opinions. Prompting a model not to fabricate does
not work, because fabrication is not a decision the model is making.

So this profile does not ask. It **extracts every citation-shaped string from
every draft and resolves it against an authority ledger of documents actually
retrieved in this matter.** A citation that does not resolve blocks the file
write, with the offending text quoted back. The same machinery blocks invented
party names, dates, dollar amounts, addresses, and deadlines.

Four gates run in code on every draft:

| Gate | Refuses |
| --- | --- |
| **Citation** | a citation not in the ledger; a statement of law with no citation |
| **Fact** | a name, date, amount, address, docket, or duration not in the matter fact table and not a `[[FACT:...]]` placeholder |
| **Jurisdiction** | out-of-jurisdiction authority described in binding language |
| **Currency** | a stale statute/regulation/rule, or a case with no treatment check |

A document delivered with fifteen bracketed blanks is a **correct** deliverable.
A fluent document with one invented case is a catastrophic one.

---

## Hats

The hat decides which documents exist, which checklists apply, and which
authority matters. Set it once per matter; the hat's conventions load on demand
via `skill_view` rather than sitting in the prompt.

`litigation` · `transactional` · `corporate` · `employment` · `ip` ·
`real-estate` · `family` · `immigration` · `estates` · `regulatory` · `pro-se`

21 document types ship in `plugins/lex/data/doc_types.json` — complaints,
answers, motions, discovery, demand letters, NDAs, MSAs, employment agreements,
offer letters, operating agreements, bylaws, board consents, cease-and-desist,
leases, wills, powers of attorney, settlement agreements, privacy policies,
compliance memos, legal memos, agency comments. Each is a **required-elements
contract**, not a fill-in template: the scaffold tells you what the document must
contain and marks every particular you have not been given.

Adding a document type is a JSON edit, not a code change. If a document is not
in the registry, `draft_scaffold` refuses and tells you to add it — deliberately,
so nobody improvises a structure for a document with statutory formalities.

---

## Install

```bash
hermes profile install ./agents/counsel-bot --alias
cp agents/counsel-bot/.env.EXAMPLE ~/.hermes/profiles/counsel-bot/.env   # then fill it
hermes memory setup
hermes plugins list
```

Set `model.default` and `delegation.model` in `config.yaml` — they ship as
placeholders on purpose. `COURTLISTENER_TOKEN` is strongly recommended: without
it, external citation verification is unavailable and every citation is reported
unverified rather than silently trusted.

---

## A run

```
matter_open      name="Acme v. Doe" jurisdiction=US-CA forum="N.D. Cal."
                 posture=pleading represented_party="Acme"
set_hat          hat=litigation                    → skill_view hat-litigation
matter_fact      key=incident_date value=2026-03-11 source=user
issue_plan       action=create issues=[...]        → one per claim element set
worker_brief     issue_index=0                     → delegate_task(tasks=[...])
authority_read   auth_id=A7 find="the elements of" → read before you cite
draft_scaffold   doc_type=complaint                → required elements + placeholders
draft_check      text=<draft> doc_type=complaint   → must return clean
write_file       path=drafts/complaint.md          → gated; refused if not clean
```

The final response gets a deterministic disclaimer footer, plus a citation
warning listing anything unverified — appended by a hook, costing zero inference
tokens, and impossible for the model to forget.

---

## What is in the box

```
SOUL.md                  identity: investigator, not oracle
config.yaml              full knob sweep — context economics, sandbox, fan-out
mcp.json                 CourtListener / govinfo / eCFR (two endpoints unverified)
plugins/lex/             15 tools · 12 hooks · 2 cache-safe prompt sections
  store/gates.py         the four gates — read this file first
  store/cites.py         citation extraction (eyecite when present, regex fallback)
  store/rules.py         deterministic date math; no model involvement
  data/doc_types.json    21 document contracts
  data/hats.json         11 practice hats with hard rules
  data/jurisdictions.json 53 US jurisdictions
  scripts/               fetch_authority · verify_citations · redline
skills/                  10 skills: intake, research, drafting, cite-check, 6 hats
evals/                   12 frozen tasks incl. 4 adversarial, rubric, CI gates
```

## Token economics

Legal sources are enormous. Nothing raw rides the context window twice: the
intake hook stores full text content-addressed on disk and hands the model a
bounded authority card with byte offsets, the dedupe fence refuses a second
fetch of the same URL, `compression.proactive_prune_tokens` stops old payloads
being re-sent every turn, retrieval children run on a cheap model and return
findings rather than opinions, and the bibliography is generated deterministically.

## Reading order for reviewers

1. `HONEST-LIMITS.md` — what this cannot do.
2. `plugins/lex/store/gates.py` — the enforcement.
3. `docs/profiles/counsel-bot-spec.md` — why each mechanism exists.
4. `evals/rubric.md` — how it is measured.
