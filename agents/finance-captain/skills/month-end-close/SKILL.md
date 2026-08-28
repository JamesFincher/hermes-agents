---
name: month-end-close
description: "Run a disciplined close: pull, reconcile, scan exceptions, explain variances, tie out, and close the period."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Close]
    requires_toolsets: [fin]
    requires_tools: [period_manage, snapshot_pull, recon_tieout, anomaly_scan, report_check]
    related_skills: [budget-and-variance, hat-controller]
---

# Month-End Close

## When to Use
Closing a period, or preparing anything labeled final.

## Quick Reference
The checklist is enforced by `period_manage`. `period_manage action=status
period=YYYY-MM` shows what remains. A close with items outstanding requires
`force=true` and a written reason, and that is recorded.

## Procedure
1. `snapshot_pull` from every system for the period: accounting, banking,
   payments, spend, payroll. Pull, do not eyeball.
2. If a prior snapshot exists for the same source and period, `snapshot_diff`
   it. **Restatements are findings.** Anything published on the old snapshot
   needs to be flagged.
3. `recon_tieout` books against bank, per account. Every unmatched item is an
   open item with an owner. Never a plug.
4. `anomaly_scan` each snapshot. Work the high-severity findings: uncategorized
   items and duplicate payments especially. Disposition each one — resolved,
   accepted with a reason, or escalated.
5. Accruals and cutoff: unbilled revenue, unrecorded liabilities, prepaid
   amortization, deferred revenue. Each is a judgment, so each gets stated as
   an assumption with its basis.
6. `metric_compute` the period metrics. Each returns an `[F#]`.
7. `variance_report` against budget. Every material line gets a **cause**, not
   a category name. "Marketing over by 40k" is not an explanation.
8. `report_scaffold report_type=month_end_close_pack`, draft citing `[F#]`,
   then `report_check` with `final=true` and the tie-out snapshot.
9. `period_manage action=check` each checklist item as you complete it, then
   `action=close`.
10. Deliver: headline, exceptions, variances with causes, open items with
    owners, and anything restated from a prior period.

## Pitfalls
- **Closing with uncategorized transactions.** They will land somewhere, and it
  will be wrong.
- **Plugging a reconciling difference.** Find it. A plug hides the error that
  will compound next month.
- **Publishing before the last pull.** A snapshot from Tuesday and a close on
  Friday means Wednesday's activity is missing.
- **Explaining variance by naming the account.** Find the transaction.

## Verification
Every checklist item green, every reconciliation ties within tolerance,
`report_check` returns clean with `final=true`, and the period shows closed.
