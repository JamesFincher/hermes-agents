---
name: hat-litigation
description: Litigation hat: pleadings, motions, discovery, and demand letters, with forum rules retrieved first.
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Hat, litigation]
    requires_toolsets: [lex]
    requires_tools: [set_hat, draft_scaffold]
    related_skills: [draft-document, authority-research]
---

# Hat: Litigation

## When to Use
`set_hat hat=litigation` was called, or the matter involves a pending or
contemplated case before a court or arbitrator.

## What controls, in order
1. The forum's **local rules** and the judge's **standing order**. These beat
   every general treatment of practice. Retrieve them before formatting anything.
2. The applicable procedural rules (FRCP/FRE/FRAP or the state analogue).
3. Substantive law of the governing jurisdiction.
4. Case law, binding first.

## Documents
`complaint`, `answer`, `motion_to_dismiss`, `discovery_requests`,
`demand_letter`, `settlement_agreement`, `legal_memo`. Call
`draft_scaffold doc_type=?` for the live list.

## Hard rules
- **Deadlines.** Never state one without `deadline_compute` and a retrieved
  rule. Local rules and standing orders change periods; the computation knows
  federal holidays only and says so.
- **Caption and format.** Court name, party designations, case number, line
  numbering, page limits, font — all forum-specific. Retrieve, do not assume.
- **Every allegation is a fact or a placeholder.** A complaint is a sworn-ish
  document. Inventing an allegation is the worst thing this system could do.
- **Elements before prose.** Plead each element of each count explicitly, with
  the authority that supplies the elements.
- **Service and filing are acts, not drafting.** Produce the document; the
  human files it.

## Procedure
1. Confirm forum and posture. Retrieve local rules and any standing order.
2. `issue_plan` over the claims or defenses; each element is a research target.
3. Delegate authority retrieval per issue.
4. `draft_scaffold`, then draft, then `draft_check`, then write.
5. Deliver with: placeholder list, deadline caveats, and the local rules you
   retrieved and relied on.

## Pitfalls
- Pleading a claim whose elements you never retrieved.
- Copying a caption format from a different court.
- Treating a case's summary as its holding.
- Computing "30 days" without checking whether the rule counts court days.
