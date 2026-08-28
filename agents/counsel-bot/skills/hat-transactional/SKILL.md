---
name: hat-transactional
description: "Transactional hat: agreements, with every commercial term sourced and jurisdiction-fatal clauses flagged."
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Hat, transactional]
    requires_toolsets: [lex]
    requires_tools: [set_hat, draft_scaffold]
    related_skills: [draft-document, authority-research]
---

# Hat: Transactional

## When to Use
`set_hat hat=transactional`. Agreements between parties: services, sales,
licensing, NDAs, settlements, leases.

## Quick Reference
`set_hat hat=transactional`, then `draft_scaffold doc_type=?`. Documents:
`nda`, `msa`, `settlement_agreement`, `lease`, `demand_letter`, `legal_memo`.
Every number is a recorded fact or a `[[FACT:...]]` placeholder.

## What controls
Party intent, expressed in the document, constrained by the governing law they
choose and by any mandatory law they cannot contract around.

## Documents
`nda`, `msa`, `settlement_agreement`, `lease`, `demand_letter`, `legal_memo`.

## Hard rules
- **Governing law and venue are decisions, not defaults.** They come from a
  recorded fact or they are placeholders. Never quietly pick Delaware.
- **Every number is a fact.** Fees, caps, terms, notice periods, cure periods.
  If you were not told it, it is `[[FACT:...]]`.
- **Mandatory law overrides the contract.** Late-fee caps, deposit handling,
  consumer protections, employee carve-outs. Flag with authority.
- **Define before you use.** A defined term used before its definition is a
  drafting defect; check the whole document at the end.
- **Symmetry check.** State plainly which side each allocation favors. You are
  drafting for the recorded represented party; say where the document is
  one-sided so the reviewer can decide deliberately.

## Procedure
1. Confirm the represented party and the deal shape.
2. Record every commercial term you were given as a fact.
3. Retrieve authority only for clauses whose enforceability is jurisdictional.
4. `draft_scaffold`, draft, `draft_check`, write.
5. Deliver with an open-terms list and a short list of clauses that need a
   business decision rather than a legal one.

## Pitfalls
- Carrying a liability cap or restrictive covenant across state lines.
- Silent auto-renewal terms in jurisdictions that regulate them.
- An indemnity that swallows the liability cap two pages later.
- Signature blocks that do not match the recorded entity names.

## Verification
Hat is `transactional`. Represented party is recorded. Open terms are listed.
`draft_check` is clean before write.
