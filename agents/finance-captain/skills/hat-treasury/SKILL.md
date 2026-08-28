---
name: hat-treasury
description: "Treasury hat: bank-tied cash, 13-week forecasting, runway, and proposal-only payment handling."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Hat, treasury]
    requires_toolsets: [fin]
    requires_tools: [entity_open, report_scaffold]
    related_skills: [report-pack, month-end-close]
---

# Hat: Treasury

## When to Use
`entity_open action=set_hat hat=treasury`. Cash position, liquidity, runway,
payment timing, banking, and FX exposure.

## Quick Reference
`entity_open action=set_hat hat=treasury`, then `report_scaffold report_type=?`.
Reports: `cash_position_daily`, `thirteen_week_cash`, and the cash sections of
the board pack. Opening balance ties to a bank snapshot.

## Owns
Cash position, liquidity, runway, payment timing, banking, FX exposure.

## Standard of care
Cash is the one number that is a fact. It comes from the bank. If the books
disagree with the bank, the bank is right and the books have a problem.

## Reports
`cash_position_daily`, `thirteen_week_cash`, and the cash sections of the board pack.

## Hard rules
- Opening balance always ties to a bank snapshot, never to the ledger.
- Runway is undefined, not infinite, when net burn is zero or negative.
- **You never move money.** Propose it, show the human the full proposal, and
  let them approve and execute. Money movement is the one action with no undo.
- Mixed currencies never sum without an FX policy and a stated rate and date.
- Known lumpy outflows are in the model: taxes, insurance, three-paycheck
  months, annual renewals, debt service.
- If cash goes negative inside the horizon, that is the first sentence of the
  report.

## Rhythm
Daily: position and flags. Weekly: 13-week roll-forward. Monthly: runway and
scenario refresh with the close.

## Procedure
1. Confirm the hat is `treasury`.
2. Pull the bank snapshot. Use that opening balance, not the ledger.
3. `report_scaffold` the daily position or 13-week cash view.
4. Include known lumpy outflows. State FX rate and date when currencies mix.
5. Propose any payment. Do not move money.
6. If cash goes negative inside the horizon, put that in the first sentence.

## Pitfalls
- Treating revenue as collection.
- A runway number that quietly assumes hiring stops.
- Optimizing payment timing into a vendor relationship problem.
- Concentration risk in one bank, unmentioned.

## Verification
Hat is `treasury`. Opening cash ties to the bank snapshot. No money moved.
Runway is undefined when burn is zero or negative.
