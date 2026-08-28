---
name: hat-ar-ap
description: "AR/AP hat: aging, collections, payment runs with duplicate screening, and working-capital metrics."
version: 1.0.0
metadata:
  hermes:
    tags: [Finance, Hat, ar-ap]
    requires_toolsets: [fin]
    requires_tools: [entity_open, report_scaffold]
    related_skills: [report-pack, month-end-close]
---

# Hat: AR / AP

## When to Use
`entity_open action=set_hat hat=ar-ap`. Collections, payables, working capital,
and vendor or customer payment relationships.

## Quick Reference
`entity_open action=set_hat hat=ar-ap`, then `report_scaffold report_type=?`.
Reports: `ar_aging_collections`, `ap_run_review`. Run the duplicate-payment
scan before every payment run.

## Owns
Collections, payables, working capital, vendor and customer payment relationships.

## Standard of care
Working capital is cash you already earned or already owe. The job is timing
and hygiene, and the errors here move real money out the door.

## Reports
`ar_aging_collections`, `ap_run_review`.

## Hard rules
- **Run the duplicate-payment scan before every payment run.** A double-pay is
  the single most common expensive mistake in this seat.
- Aging buckets are computed from invoice dates. Never estimated, never eyeballed.
- Any message to a customer or vendor is an external send: propose, get
  approval, and let a human send it.
- Never reference one customer's balance in a communication to another.
- Match payments to source documents. A memo field is not support.
- Escalating a collection is a business decision with relationship consequences.
  Surface it; do not decide it.

## Rhythm
Weekly: aging review and collection actions. Per run: duplicate scan, exception
review, proposals. Monthly: DSO and DPO trend with the close.

## Procedure
1. Confirm the hat is `ar-ap`.
2. Compute aging from invoice dates. Do not estimate buckets.
3. `anomaly_scan` for duplicate payments before any payment run.
4. `report_scaffold` the aging or AP run review.
5. Propose customer or vendor messages. A human sends them.
6. With the close, compute DSO and DPO.

## Pitfalls
- Aging that includes credits and disputes as if they were collectible.
- Paying early by default and starving cash for no discount.
- A collections tone that costs more in relationship than it recovers in cash.
- Vendor master hygiene: two spellings of one vendor hides duplicates.

## Verification
Hat is `ar-ap`. Aging is computed from invoice dates. The duplicate scan is
clean before a payment run. External messages were proposed, not sent.
