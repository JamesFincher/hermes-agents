---
name: report-pack
description: Assemble any report so that every number ties to a figure and the totals reconcile to their snapshot.
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Reporting]
    requires_toolsets: [fin]
    requires_tools: [report_scaffold, report_check, metric_compute, figure_check]
    related_skills: [month-end-close, hat-investor-reporting]
---

# Report Pack

## When to Use
Producing any deliverable that leaves your hands: board pack, investor update,
close package, KPI dashboard, diligence file.

## Quick Reference
`report_scaffold report_type=?`, compute figures first, draft with `[F#]`,
then `report_check` until clean. Write to `reports/`. The write is gated.

## The rule that governs everything here
Every number in the document carries an `[F#]` whose stored value matches. The
gate checks both existence and match — so a number copied forward from last
month's deck after the data changed gets caught, which is the failure that
actually happens.

## Procedure
1. `report_scaffold report_type=?` to see what the hat allows, then scaffold
   the type. It returns required sections, required metrics, and the tie-out.
2. Compute everything first. `metric_compute` and `ledger_query` each return an
   `[F#]`. Do not start writing until the figures exist — writing first invites
   filling numbers from memory.
3. Draft. Cite `[F#]` next to every number. Anything you cannot compute is
   `[[EST: basis]]` or `[[TBD: what is missing]]`, and both are acceptable
   outputs.
4. `report_check` with `snapshots`, `report_totals`, `tie_to`, and `final`.
   Fix every finding. Re-run until clean.
5. Write to `reports/`. The write is gated.
6. For a formatted deliverable, build the workbook deterministically:
   `python3 ${HERMES_SKILL_DIR}/../../plugins/fin/scripts/build_xlsx.py spec.json out.xlsx`
7. Deliver with: period, basis, snapshot ids, what is preliminary, what was
   restated since last time, and the open items.

## Pitfalls
- **Rounding differences that look like errors.** Round once, at presentation,
  from cents. Never round intermediates.
- **A metric that changed definition.** The gate requires the version. If the
  definition changed, say so and restate the prior period on the new basis.
- **Charts without the underlying figures.** A chart is a number too.
- **Publishing on an unclosed period without the preliminary label.**

## Verification
`report_check` clean, totals tie to the named snapshot, every metric carries
its version, and the preliminary label is present when the period is open.
