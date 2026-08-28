---
name: budget-and-variance
description: Build budgets and explain variances by cause, not by category name.
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, FP&A]
    requires_toolsets: [fin]
    requires_tools: [budget_manage, variance_report, ledger_query, report_check]
    related_skills: [cash-forecast, hat-fpa]
---

# Budget and Variance

## When to Use
Building or revising a budget, and every period-end variance review.

## Quick Reference
`budget_manage action=set` for lines. At period end, `variance_report` then
`ledger_query` for each material cause. Classify timing, permanent, or error.
`report_scaffold report_type=budget_vs_actual` and `report_check`.

## Procedure
1. `budget_manage action=set` with the period's lines. Budgets are account
   level; if the operator gives you departmental targets, map them to accounts
   or the variance report will not tie.
2. At period end, `variance_report period=YYYY-MM snapshot=<actuals>`. It
   returns every line plus the material ones flagged, and records an `[F#]` per
   material variance.
3. For each material line, find the **cause** by drilling in:
   `ledger_query snapshot=... filters={"account": "..."} group_by=vendor`.
   Then look at the actual transactions. The cause is almost always one or two
   specific items: a timing shift, a renewal that landed early, a one-off, a
   headcount change, a rate change.
4. Classify each: **timing** (it reverses), **permanent** (it does not),
   or **error** (fix it in the books, do not explain it in the report).
5. Update the forecast for anything permanent. A variance you explain but do
   not roll forward will reappear every month.
6. `report_scaffold report_type=budget_vs_actual`, draft with `[F#]`, then
   `report_check`.

## Pitfalls
- **Percentage variance on a small base.** 400% over on a $200 line is noise;
  materiality is in dollars, and the tool uses the configured threshold.
- **Sign conventions.** Over-spend on an expense and under-delivery on revenue
  are both unfavorable but have opposite arithmetic signs. Say favorable or
  unfavorable in words.
- **Budget that never gets re-baselined.** State whether you are comparing to
  the original budget or the current forecast, every time.

## Verification
Total variance in the report equals the sum of the line variances, every
material line has a named cause, and `report_check` is clean.
