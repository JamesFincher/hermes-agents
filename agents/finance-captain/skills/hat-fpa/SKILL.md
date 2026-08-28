---
name: hat-fpa
description: "FP&A hat: budgets, driver-based forecasts, and variances explained by cause with downside cases."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Hat, fpa]
    requires_toolsets: [fin]
    requires_tools: [entity_open, report_scaffold]
    related_skills: [report-pack, month-end-close]
---

# Hat: FP&A

## When to Use
`entity_open action=set_hat hat=fpa`. Budget, rolling forecast, variance
analysis, scenarios, and the metrics the board sees.

## Quick Reference
`entity_open action=set_hat hat=fpa`, then `skill_view budget-and-variance`.
Reports: `budget_vs_actual`, `board_pack`, `kpi_dashboard`, `flux_analysis`.
Every material variance gets a cause traced to transactions.

## Owns
Budget, rolling forecast, variance analysis, scenarios, the metrics the board sees.

## Standard of care
Numbers are the easy part. The job is the **cause**: which specific thing
happened, whether it reverses, and what it means for the rest of the year.

## Reports
`budget_vs_actual`, `board_pack`, `kpi_dashboard`, `flux_analysis`.

## Hard rules
- Every material variance gets a cause traced to transactions, not a category name.
- Classify every variance: timing, permanent, or error. Permanent ones update
  the forecast in the same session, or they will reappear next month.
- Forecasts are driver-based, come with assumptions, and always include a
  downside. Never a point estimate presented as fact.
- A metric definition change is a version bump plus a restatement of the prior
  periods on the new basis. Never a quiet recalculation.
- Say whether you are comparing to original budget or current forecast.

## Rhythm
Monthly: variance and forecast update. Quarterly: re-baseline, scenario refresh.
Annually: the budget build, bottoms-up by driver.

## Procedure
1. Confirm the hat is `fpa`.
2. Follow `budget-and-variance` for the period review.
3. Classify each material variance: timing, permanent, or error.
4. Update the forecast in the same session for permanent items.
5. `report_scaffold` the board pack or KPI dashboard with a downside case.

## Pitfalls
- Percentage variance on a tiny base treated as material.
- A forecast nobody can challenge because the assumptions are buried.
- Optimism laundering: three "conservative" assumptions stacked into a base case.
- Explaining the same variance three months running without fixing the forecast.

## Verification
Hat is `fpa`. Every material variance has a named cause. Permanent items updated
the forecast. Comparison basis (budget vs forecast) is stated.
