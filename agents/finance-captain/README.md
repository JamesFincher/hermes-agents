# finance-captain

A Hermes profile that wires into the business systems, runs the books, and
**refuses to publish a number that does not trace**.

> Not a CPA, not an auditor, not an adviser. It does not give investment, tax,
> or securities advice, and it does not write to any system of record without a
> human approving that specific action. See `HONEST-LIMITS.md`.

---

## The one idea

In research, the fabrication failure is an invented citation. In finance, it is
subtler and more expensive: **a number that used to be right.** Somebody
computes revenue on Tuesday, drops it in a deck, the data changes Wednesday, and
the deck goes to the board on Friday still saying Tuesday's number. Nobody lied.
Everybody is wrong.

So every computed value becomes a **figure** with an id, a formula, its inputs,
and the snapshot it came from. Reports cite them inline:

```
Revenue for July was $1,240,338.00 [F1] and gross profit was $920,338.00 [F2].
```

The gate extracts every currency amount, percentage, and ratio in the draft and
checks it against the figure it cites. Live output from the shipped test:

```
Report refused. Fix these before it can be written:
  NUMBER    $84,200.00 has no [F#] behind it. compute it with metric_compute...
  NUMBER    12.4% has no [F#] behind it...
```

and, for the stale-copy case:

```
  MISMATCH  $1,199,000.00 does not match F1=$1,240,338.00 — the number in the
            text does not match the figure it cites — recompute, or the data
            moved under a copied number
```

That second one is the whole point. It catches the error that actually happens.

## Four gates on every report write

| Gate | Refuses |
|---|---|
| **Number fence** | a number with no `[F#]`, or one that doesn't match the figure it cites |
| **Tie-out** | report totals that don't reconcile to their snapshot within tolerance |
| **Freshness** | a stale snapshot, or a `final` report on an unclosed period |
| **Definitions** | a metric named without its registry version |

Plus a **mutation fence**: the profile cannot write to QuickBooks, Stripe, or a
bank. It *proposes*, with a dry run and a rationale; a human approves that
specific proposal id; only then does it apply, once, under an idempotency key.
Money movement needs a second confirmation on top. Default mode is
`propose_only` — it cannot execute at all until an administrator changes that.

## Hats

`controller` · `fpa` · `treasury` · `ar-ap` · `investor-reporting` ·
`bookkeeping`

Each hat gates which of the **12 report types** are available and loads its own
conventions on demand: close packs, board packs, investor updates, 13-week cash,
budget vs actual, AR aging, AP run review, daily cash, KPI dashboards,
categorization batches, audit prep, flux analysis.

## Determinism

Nothing that can be computed is prompted. The model never does arithmetic.

- **Money is integer cents**, never a float, with a currency. Mixed-currency
  sums are refused without an FX rate and date.
- **The metric registry** defines ARR, MRR, NRR, gross margin, operating income,
  net burn, runway, DSO, DPO, quick ratio, CAC, LTV/CAC, and variance — one
  definition each, versioned, formula in code. Runway when burn is negative
  returns *undefined*, not infinity.
- **Anomaly detection** is arithmetic: duplicate vendor payments, z-score
  outliers, uncategorized items, suspicious round numbers at material size,
  weekend entries, and a Benford check that refuses to report on populations too
  small to mean anything.
- **Forecasting** is a driver roll-forward that tells you which month cash goes
  negative. It has no opinion about whether your drivers are right — its job is
  to make them explicit enough to argue with.

## Install

```bash
hermes profile install ./agents/finance-captain --alias
cp agents/finance-captain/.env.EXAMPLE ~/.hermes/profiles/finance-captain/.env
hermes memory setup
hermes plugins list
```

Set `model.default` and `delegation.model` — they ship as placeholders. Grant
**read-only scopes** on every connected system. Most MCP endpoints in
`mcp.json` are marked UNVERIFIED; confirm or delete each at install. A missing
server is survivable (CSV loading works); a write-scoped credential is not.

## A close

```
entity_open       name="Northwind" home_currency=USD basis=accrual
entity_open       action=set_hat hat=controller      → skill_view hat-controller
snapshot_pull     source=quickbooks period=2026-07   → S1
snapshot_pull     source=plaid kind=balances         → S2
snapshot_diff     old=S0 new=S1                      → restatements are findings
anomaly_scan      snapshot=S1                        → duplicates, uncategorized
recon_tieout      snapshot_a=S1 snapshot_b=S2        → books vs bank
metric_compute    metric=gross_margin inputs={...}   → [F7]
variance_report   period=2026-07 snapshot=S1         → material lines + figures
report_scaffold   report_type=month_end_close_pack
report_check      final=true tie_to=S1               → must be clean
write_file        path=reports/close-2026-07.md      → gated
period_manage     action=close period=2026-07
```

## What's in the box

```
plugins/fin/         18 tools · 12 hooks · 2 cache-safe prompt sections
  store/gates.py     the four gates — read this first
  store/money.py     integer cents; no floats in the money path
  store/metrics.py   the metric registry, versioned, formulas in code
  store/snapshot.py  immutable point-in-time pulls + restatement diff
  store/figures.py   figure provenance — the [F#] system
  store/mutations.py propose / approve / apply-once
  store/anomaly.py   deterministic exception detection
  data/              12 report types, 6 hats, COA mapping
  scripts/           load_csv · build_xlsx · fx
skills/              12: onboarding, close, budget, forecast, reporting,
                     anomaly review, and 6 hats
evals/               12 tasks, 4 adversarial, rubric, CI gates
```

## Reading order for reviewers

1. `HONEST-LIMITS.md` — especially §2, on what the fence does *not* catch.
2. `plugins/fin/store/gates.py` — the enforcement.
3. `plugins/fin/store/metrics.py` — the definitions your org will argue about.
4. `evals/rubric.md` — how it's measured.
