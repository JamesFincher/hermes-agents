---
name: anomaly-review
description: "Work the deterministic exception scan: duplicates, outliers, uncategorized items, and shape checks."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Controls]
    requires_toolsets: [fin]
    requires_tools: [anomaly_scan, ledger_query, mutation_propose]
    related_skills: [month-end-close, hat-bookkeeping]
---

# Anomaly Review

## When to Use
Every close, before every payment run, and any time someone asks whether the
numbers look right.

## Quick Reference
`anomaly_scan snapshot=<id>`. Work high severity first. Uncategorized blocks
the close. Duplicate payments block a payment run. Disposition each finding:
resolved, accepted, or escalated.

## What the scan actually does
Deterministic arithmetic, no model, no tokens: duplicate vendor payments,
statistical outliers by account, uncategorized and suspense items, suspiciously
round material amounts, weekend entries, and a Benford first-digit shape check
on populations large enough to mean anything.

## Procedure
1. `anomaly_scan snapshot=<id>`.
2. Work high severity first. **Uncategorized** items block the close; they
   cannot be reported. **Duplicate payments** block a payment run; a double-pay
   that goes out takes weeks to claw back.
3. For each finding, open the underlying items with `ledger_query
   include_rows=true` and look. The scan raises a question; it never answers one.
4. Disposition every finding explicitly: resolved (with what changed), accepted
   (with why it is fine), or escalated (to whom).
5. If a fix is needed in the source system, `mutation_propose` it. You do not
   edit books directly.

## Pitfalls
- **Treating a finding as an accusation.** These are statistical and structural
  signals. A duplicate flag is usually a legitimate recurring charge. Check
  before you say anything about it to anyone.
- **Benford on a small or constrained population.** It means nothing under a
  few hundred natural amounts, and nothing at all on data with fixed price
  points. The tool refuses to report it when it does not apply.
- **Clearing uncategorized items by guessing.** Ask. An unresolved item flagged
  is honest; a wrong category is a silent error in every downstream report.

## Verification
Every high-severity finding has a disposition. Uncategorized is empty before
close. The payment run has a clean duplicate check.
