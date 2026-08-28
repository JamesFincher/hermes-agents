---
name: hat-corporate
description: "Corporate hat: formation, governance, and equity documents anchored to the state entity statute."
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Hat, corporate]
    requires_toolsets: [lex]
    requires_tools: [set_hat, draft_scaffold]
    related_skills: [draft-document, authority-research]
---

# Hat: Corporate

## When to Use
`set_hat hat=corporate`. Formation, governance, equity, and entity maintenance.

## Quick Reference
`set_hat hat=corporate`, then `draft_scaffold doc_type=?`. Documents:
`operating_agreement`, `bylaws`, `board_consent`, `nda`, `msa`,
`employment_agreement`, `legal_memo`. Anchor each statutory floor to the
formation-state entity code.

## What controls
The state entity statute first: it supplies defaults, mandatory rules, and which
defaults may be varied by agreement. Then the charter, then the bylaws or
operating agreement, then board and shareholder action.

## Documents
`operating_agreement`, `bylaws`, `board_consent`, `nda`, `msa`,
`employment_agreement`, `legal_memo`.

## Hard rules
- **Cite the code section.** Notice periods, quorum minimums, indemnification
  limits, and written-consent authority are statutory. Retrieve them.
- **Know which defaults are waivable.** Varying a mandatory rule by agreement is
  a void provision, not a clever one.
- **Securities implications are flagged, never resolved.** Any issuance,
  transfer, or compensation-in-equity question gets a flag and a referral.
- **Never state a filing fee, processing time, or form edition from memory.**

## Procedure
1. Confirm entity type and formation state — they change everything downstream.
2. Retrieve the governing entity statute for each provision that has a
   statutory floor.
3. `draft_scaffold`, draft, `draft_check`, write.
4. Deliver with: the statutory sections relied on, the provisions that vary a
   default, and any securities or tax question you flagged.

## Pitfalls
- Delaware bylaws dropped onto a non-Delaware entity.
- Indemnification broader than the statute permits.
- Written consent used where the statute requires unanimity.
- Cap-table math done in prose. Use `execute_code`.

## Verification
Hat is `corporate`. Entity type and formation state are recorded. Statutory
floors cite the code. `draft_check` is clean before write.
