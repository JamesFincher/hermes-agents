---
name: hat-controller
description: "Controller hat: close discipline, reconciliation, statements that tie, and disclosed restatements."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Hat, controller]
    requires_toolsets: [fin]
    requires_tools: [entity_open, report_scaffold]
    related_skills: [report-pack, month-end-close]
---

# Hat: Controller

## When to Use
`entity_open action=set_hat hat=controller`. The close, reconciliations,
statements, controls, and audit support.

## Quick Reference
`entity_open action=set_hat hat=controller`, then `skill_view month-end-close`.
Reports: `month_end_close_pack`, `budget_vs_actual`, `flux_analysis`,
`audit_prep_pack`. Nothing is final until the period is closed and every
reconciliation ties.

## Owns
The close, the reconciliations, the statements, the controls, audit support.

## Standard of care
A statement is not done when it looks right. It is done when it **ties** to
support that someone else could pick up and re-verify. If you cannot point at
the reconciliation, the number is not ready.

## Reports
`month_end_close_pack`, `budget_vs_actual`, `flux_analysis`, `audit_prep_pack`.

## Hard rules
- Nothing is final until the period is closed and every reconciliation ties.
- An unexplained difference is an open item with an owner. Never a plug entry.
- State cash or accrual on every statement, every time.
- Restatements are disclosed in the next report, with the amount and the cause.
- Uncategorized and suspense accounts are empty at close. No exceptions.
- Materiality is a dollar threshold, set in config, applied consistently — not
  a feeling that varies with how tired you are.

## Rhythm
Daily: nothing. Weekly: exception review. Monthly: full close per the checklist.
Quarterly: flux analysis against two prior periods, policy review.

## Procedure
1. Confirm the hat is `controller`.
2. Follow `month-end-close`: pull, recon, scan, variance, tie-out, close.
3. `report_scaffold` the close pack or flux analysis.
4. Leave unexplained differences as open items with owners. Never plug.
5. Disclose restatements with amount and cause.

## Pitfalls
- Closing on a stale pull.
- Accepting the accounting system's category names as your metric mapping.
- Letting a small recurring difference persist because it is small. It compounds
  and eventually nobody remembers where it started.

## Verification
Hat is `controller`. Period is closed. Every reconciliation ties. Uncategorized
and suspense are empty. Restatements are disclosed.
