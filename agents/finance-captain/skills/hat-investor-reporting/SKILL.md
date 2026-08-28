---
name: hat-investor-reporting
description: "Investor reporting hat: consistent registry metrics, disclosed restatements, and assumptions attached to anything forward-looking."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Hat, investor-reporting]
    requires_toolsets: [fin]
    requires_tools: [entity_open, report_scaffold]
    related_skills: [report-pack, month-end-close]
---

# Hat: Investor Reporting

## When to Use
`entity_open action=set_hat hat=investor-reporting`. Board decks, investor
updates, KPI dashboards, and diligence packages.

## Quick Reference
`entity_open action=set_hat hat=investor-reporting`, then `skill_view
report-pack`. Reports: `board_pack`, `investor_update`, `kpi_dashboard`. Use
registry definitions with versions, the same every period.

## Owns
Board decks, investor updates, KPI dashboards, diligence packages.

## Standard of care
Consistency across periods matters more than any single number. An investor
reading four quarters of your reporting should be able to compare them without
adjusting anything.

## Reports
`board_pack`, `investor_update`, `kpi_dashboard`.

## Hard rules
- Registry definitions, with versions, the same every period. If a definition
  changed, say so and restate the prior periods on the new basis.
- **If a number moved from last quarter's deck, say it moved, by how much, and
  why.** Investors find these. Finding it yourself is the whole difference.
- Every forward-looking statement carries its assumptions in the body.
- Lowlights before highlights. Bad news that arrives late costs credibility
  that the number itself never would have.
- This is reporting, not an offer, a solicitation, or securities advice.
- No metric invented for one deck to make a trend look better. If a new metric
  is genuinely useful, add it to the registry and backfill prior periods.

## Rhythm
Monthly: investor update. Quarterly: board pack. Ad hoc: diligence.

## Procedure
1. Confirm the hat is `investor-reporting`.
2. `report_scaffold` the board pack, investor update, or KPI dashboard.
3. Cite registry metrics with versions. Restate prior periods if a definition
   changed.
4. If a number moved from last quarter's deck, say it moved, by how much, and
   why.
5. Put assumptions for forward-looking statements in the body. Lowlights first.

## Pitfalls
- The definition drift that makes this quarter incomparable to last.
- A cherry-picked cohort or window with no note that it is one.
- Charts whose axes changed between decks.
- Burying the cash number.

## Verification
Hat is `investor-reporting`. Metrics carry registry versions. Restatements are
disclosed. Forward-looking statements include assumptions in the body.
