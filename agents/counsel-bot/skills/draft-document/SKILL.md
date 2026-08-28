---
name: draft-document
description: Assemble any legal document from its required-elements contract, with placeholders instead of invented facts, and pass the gates before writing.
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Drafting, Documents]
    requires_toolsets: [lex, file]
    requires_tools: [draft_scaffold, draft_check, cite_format, matter_fact]
    related_skills: [authority-research, cite-check]
---

# Draft a Document

## When to Use
The matter is open, the hat is set, and the authority for any legal assertion in
the document has been retrieved. If any of those is untrue, you are drafting too
early.

## Quick Reference
`draft_scaffold` → draft with `[[FACT:...]]` blanks → `cite_format` →
`draft_check` until clean → write under `drafts/`. Never fill a placeholder
with a plausible value.

## Procedure
1. `draft_scaffold doc_type=?` to see what this hat allows. Then
   `draft_scaffold doc_type=<key>` for the required-elements contract.
2. Look at `missing_facts`. For each: either `matter_fact` it (if you were told
   it) or leave the `[[FACT:...]]` placeholder in the draft. **Never fill a
   placeholder with a plausible value.** A document delivered with fifteen
   bracketed blanks is a correct deliverable.
3. Write section by section in the scaffold's order. For every section with
   `authority_required: true`, cite the authority you retrieved. Quote from
   `authority_read`, not from memory and not from a card.
4. Generate citations with `cite_format` — do not hand-write a citation string.
5. `draft_check text=<draft> doc_type=<key>` before any file write. Fix every
   finding. Re-run until `verdict: clean`.
6. Write to `drafts/<name>.md`. The write is gated: if the gates fail, the write
   is refused with the offending text quoted.
7. Deliver with: the open placeholders listed, the assumptions you made, the
   authorities relied on, and what a reviewing attorney must check first.

## Pitfalls
- **Boilerplate carried across jurisdictions.** A clause that is standard in one
  state can be void in another. Restrictive covenants, liability caps, late
  fees, and deposit terms are the usual killers.
- **Filling a blank to make the document read well.** This is the single failure
  mode this profile exists to prevent. Fluency is not a value here.
- **Citing a case for a proposition you inferred from its summary.** Open it.
- **Computing a deadline inline.** Use `deadline_compute` with a retrieved rule,
  or state that the deadline must be confirmed.

## Verification
`draft_check` returns clean, the placeholder list is stated to the user, and
every `authority_required` section has a citation that resolves in the ledger.
