---
name: hat-employment
description: "Employment hat: federal floor and state ceiling checked separately, with jurisdiction-fatal clauses flagged."
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Hat, employment]
    requires_toolsets: [lex]
    requires_tools: [set_hat, draft_scaffold]
    related_skills: [draft-document, authority-research]
---

# Hat: Employment

## When to Use
`set_hat hat=employment`. Offer letters, employment and contractor agreements,
policies, separation agreements, and workplace claims.

## Quick Reference
`set_hat hat=employment`, then `draft_scaffold doc_type=?`. Documents:
`employment_agreement`, `offer_letter`, `nda`, `settlement_agreement`,
`demand_letter`, `compliance_memo`, `legal_memo`. Check federal floor and
state ceiling for every statutory clause.

## What controls
A federal floor and a state (often city) ceiling. Both must be checked, and the
answer must say which one controls the point.

## Documents
`employment_agreement`, `offer_letter`, `nda`, `settlement_agreement`,
`demand_letter`, `compliance_memo`, `legal_memo`.

## Hard rules
- **Two-layer check, always.** Federal statute or regulation, then the state
  analogue, then any local ordinance. State the controlling one.
- **Restrictive covenants do not travel.** Enforceability is state-specific and
  changes frequently. Never carry a noncompete clause between jurisdictions
  without retrieving current law.
- **Classification is a test, not a label.** Exempt/non-exempt and
  employee/contractor require the specific regulation applied to recorded facts.
- **Release scope has statutory carve-outs.** Certain claims cannot be waived,
  and waivers of some claims require specific language and consideration
  periods. Retrieve the requirement.
- **Final pay, notice, and wage-statement rules are jurisdictional.** Flag them.

## Procedure
1. Confirm work location(s) — that, not the employer's HQ, usually drives the law.
2. Retrieve federal and state authority for each clause with a statutory floor.
3. `draft_scaffold`, draft, `draft_check`, write.
4. Deliver with a jurisdiction table: clause, controlling law, citation, risk.

## Pitfalls
- Remote employees in a state nobody mentioned.
- A confidentiality clause that reads as barring protected disclosures.
- Assuming at-will language cures a fixed-term promise elsewhere in the document.
- A separation agreement missing a required consideration or revocation period.

## Verification
Hat is `employment`. Work location is recorded. Each statutory clause names
the controlling federal or state source. `draft_check` is clean before write.
