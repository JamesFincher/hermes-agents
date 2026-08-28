---
name: cash-forecast
description: Deterministic driver-based cash forecasting from a bank-tied opening balance, with scenarios and stated assumptions.
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Treasury]
    requires_toolsets: [fin]
    requires_tools: [cash_forecast, metric_compute, snapshot_pull, report_check]
    related_skills: [budget-and-variance, hat-treasury]
---

# Cash Forecast

## When to Use
Runway questions, a 13-week cash view, fundraising prep, or any decision whose
answer depends on when the money runs out.

## Quick Reference
Opening balance from the bank snapshot. `cash_forecast opening_cash=...
months=13 drivers={...}`. Run base, downside, and the operator's scenario.
If cash goes negative inside the horizon, that is the headline.

## Procedure
1. **Opening balance from the bank, not the books.** Pull it. Cash is the one
   number where the bank is authoritative and a reconciliation difference does
   not get to be an opinion.
2. Build drivers explicitly: revenue by month, collection lag from actual DSO
   (`metric_compute metric=dso`), COGS as a percentage, opex by month including
   known hires and known renewals.
3. `cash_forecast opening_cash=... months=13 drivers={...}`. It rolls forward
   deterministically and tells you the month cash goes negative, if it does.
4. Run at least three cases: base, downside (collections slip a month, revenue
   flat), and the specific scenario the operator is actually asking about.
5. If cash goes negative inside the horizon, **that is the headline.** It goes
   in the first sentence, not in a section on page four.
6. State every assumption in the report body. A forecast whose assumptions are
   in a footnote is a forecast nobody can challenge.

## Pitfalls
- **Booking revenue as cash.** Revenue is not collection. The lag is the whole
  point of the exercise.
- **Forgetting the lumpy items.** Annual insurance, tax payments, payroll's
  three-paycheck months, deferred hardware. These sink forecasts.
- **A point estimate presented as a fact.** Always a range, always assumptions.
- **Runway when burn is negative.** That is cash-flow positive, and runway is
  undefined, not infinite. The metric returns that explicitly.

## Verification
Opening balance ties to the bank snapshot. Ending balances roll correctly
month to month. Assumptions are stated in the report. `report_check` is clean.
