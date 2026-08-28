---
name: entity-onboarding
description: "Establish the entity: currency, accounting basis, systems of record, COA mapping, and metric definitions."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Onboarding]
    requires_toolsets: [fin]
    requires_tools: [entity_open, snapshot_pull, recon_tieout, metric_registry]
    related_skills: [month-end-close, hat-controller]
---

# Entity Onboarding

## When to Use
First contact with a business, or any time the books, the systems, or the
chart of accounts change materially. Nothing else runs until this does.

## Quick Reference
`entity_open` with name, home currency, and basis. Then `set_hat`, map the
COA, `snapshot_pull` one period per system, `recon_tieout` books against bank
for a closed prior month, and walk `metric_registry` with the operator.

## Why it gates everything
Currency, basis, fiscal calendar, and the COA mapping decide what every
downstream number *means*. A gross margin computed against a wrong COA mapping
is confidently, precisely wrong — the worst kind.

## Procedure
1. `entity_open` with name, home currency, and basis. **Basis is not optional.**
   Cash and accrual produce different numbers for the same month, and mixing
   them silently is the most common reporting error there is.
2. `entity_open action=set_hat`, then `skill_view` the matching hat skill.
3. Inventory the systems of record: accounting, banking, payments, spend,
   payroll, warehouse. Record which system is authoritative for what. When two
   systems disagree, you need to already know which one wins.
4. Map the chart of accounts into `plugins/fin/data/coa_map.json` categories.
   Walk the actual account list; do not assume standard numbering.
5. `snapshot_pull` one period from each system as a smoke test. Confirm row
   counts and totals look sane against what the operator expects.
6. `recon_tieout` books against bank for a closed prior month. If it does not
   tie, that is your first finding, before any reporting begins.
7. Record the accounting policies that matter: revenue recognition, what goes
   in COGS, capitalization thresholds, accrual conventions. These live as
   entity assumptions and get restated in reports that depend on them.
8. `metric_registry` — walk the definitions with the operator. If their ARR is
   not the registry ARR, resolve it now, in writing.

## Pitfalls
- **Assuming the QuickBooks category names map to your metric buckets.** They
  usually do not. Hosting in "Utilities" wrecks gross margin.
- **Multi-entity.** Separate entities are separate `entity_open` calls.
  Consolidation is its own exercise with eliminations, not a summation.
- **Foreign currency.** If any account is not the home currency, establish the
  FX policy and the rate source before the first report, not during it.

## Verification
`entity_open action=status` shows basis, currency, systems, and periods. A
prior month ties books to bank. The operator has confirmed the metric
definitions in writing.
