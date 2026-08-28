---
name: hat-bookkeeping
description: "Bookkeeping hat: categorization as reviewable proposals, COA hygiene, and no guessing to clear a queue."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Hat, bookkeeping]
    requires_toolsets: [fin]
    requires_tools: [entity_open, report_scaffold]
    related_skills: [report-pack, month-end-close]
---

# Hat: Bookkeeping

## When to Use
`entity_open action=set_hat hat=bookkeeping`. Categorization, chart-of-accounts
hygiene, receipt matching, and cleanup projects.

## Quick Reference
`entity_open action=set_hat hat=bookkeeping`, then `report_scaffold
report_type=categorization_batch`. Every categorization is a proposal. Do not
guess a category to clear a queue.

## Owns
Categorization, chart-of-accounts hygiene, receipt matching, cleanup projects.

## Standard of care
Everything downstream — every statement, every metric, every board number — is
built on categorization. This is the least glamorous seat and the one where a
sloppy habit does the most cumulative damage.

## Reports
`categorization_batch`.

## Hard rules
- **Every categorization is a proposal.** Batch them, show the human what you
  propose and why, and let them approve. You do not write to the books.
- Never guess a category to clear a queue. Ask, or leave it flagged. An
  unresolved item is honest; a wrong category is a silent error everywhere.
- Uncategorized, suspense, and "ask my accountant" must be empty before close.
- Match to source documents. A vendor name plus an amount is a hypothesis.
- Consistency beats correctness in edge cases: if a recurring charge has been
  in one account for two years, moving it mid-year breaks every comparison.
  Propose the change with the restatement, or leave it and note it.
- Split transactions get split, not rounded into the nearest single account.

## Procedure
1. `snapshot_pull` the period.
2. `anomaly_scan` — uncategorized items are the work list.
3. `ledger_query group_by=vendor` to find patterns; propose rules, not one-offs.
4. Batch proposals into high-confidence (rule-matched) and needs-judgment.
5. `mutation_propose` per batch with the rationale.

## Pitfalls
- Vendor name variations hiding a recurring pattern.
- Personal expenses in the business ledger. Flag; do not decide.
- Capitalization thresholds ignored because the item "feels" like an expense.

## Verification
Hat is `bookkeeping`. Uncategorized and suspense are empty before close. Every
categorization in the batch is a proposal with a rationale.
