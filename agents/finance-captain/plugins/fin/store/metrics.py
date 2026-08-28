"""Metric registry: one definition per metric, in code, versioned.

The most expensive recurring argument in a finance org is "why is your ARR
different from mine." The answer is always that two people used two
definitions. So a definition lives here, has a version, and every figure
computed from it records which version produced it. Change the definition and
every report built on the old one is flagged, not silently superseded.
"""
from __future__ import annotations
from . import money

# name -> (version, description, required_inputs, fn)
_REG: dict = {}


def metric(name, version, description, inputs):
    def deco(fn):
        _REG[name] = {"name": name, "version": version, "description": description,
                      "inputs": inputs, "fn": fn,
                      "formula": (fn.__doc__ or "").strip()}
        return fn
    return deco


def registry() -> dict:
    return {k: {i: v[i] for i in ("name", "version", "description", "inputs", "formula")}
            for k, v in _REG.items()}


def compute(name: str, inputs: dict) -> dict:
    spec = _REG.get(name)
    if not spec:
        return {"error": f"unknown metric '{name}'", "available": sorted(_REG)}
    missing = [i for i in spec["inputs"] if i not in inputs]
    if missing:
        return {"error": f"missing inputs for {name}: {missing}",
                "formula": spec["formula"]}
    try:
        out = spec["fn"](**{k: inputs[k] for k in spec["inputs"]})
    except ZeroDivisionError:
        return {"error": f"{name}: denominator is zero — the metric is undefined, not 0"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{name}: {type(e).__name__}: {e}"}
    return {"metric": name, "version": spec["version"], "formula": spec["formula"],
            "inputs": inputs, **out}


# ── revenue / growth ─────────────────────────────────────────────────────────
@metric("mrr", "1.0", "Monthly recurring revenue from active subscriptions",
        ["subscription_amounts_cents"])
def _mrr(subscription_amounts_cents):
    """sum(normalized monthly value of every active recurring subscription)"""
    return {"value_cents": sum(int(x) for x in subscription_amounts_cents), "unit": "cents"}


@metric("arr", "1.0", "Annual recurring revenue = MRR x 12", ["mrr_cents"])
def _arr(mrr_cents):
    """MRR * 12. Not trailing revenue, not bookings, not contract value."""
    return {"value_cents": int(mrr_cents) * 12, "unit": "cents"}


@metric("net_revenue_retention", "1.0",
        "NRR = (start MRR + expansion - contraction - churn) / start MRR",
        ["start_mrr_cents", "expansion_cents", "contraction_cents", "churn_cents"])
def _nrr(start_mrr_cents, expansion_cents, contraction_cents, churn_cents):
    """(start + expansion - contraction - churn) / start. Excludes new logos."""
    s = int(start_mrr_cents)
    end = s + int(expansion_cents) - int(contraction_cents) - int(churn_cents)
    return {"raw": round(end / s, 4), "unit": "ratio", "value_cents": None,
            "pct": f"{(end / s) * 100:.1f}%"}


# ── margin / profitability ───────────────────────────────────────────────────
@metric("gross_margin", "1.0", "Gross margin = (revenue - COGS) / revenue",
        ["revenue_cents", "cogs_cents"])
def _gm(revenue_cents, cogs_cents):
    """(revenue - COGS) / revenue. COGS per the COA mapping, hosting included."""
    r, c = int(revenue_cents), int(cogs_cents)
    return {"value_cents": r - c, "unit": "cents", "raw": round((r - c) / r, 4),
            "pct": money.pct(r - c, r)}


@metric("operating_income", "1.0", "Revenue - COGS - operating expenses",
        ["revenue_cents", "cogs_cents", "opex_cents"])
def _oi(revenue_cents, cogs_cents, opex_cents):
    """revenue - COGS - opex. Excludes interest, taxes, depreciation policy items."""
    v = int(revenue_cents) - int(cogs_cents) - int(opex_cents)
    return {"value_cents": v, "unit": "cents"}


# ── cash / survival ──────────────────────────────────────────────────────────
@metric("net_burn", "1.0", "Net burn = cash out - cash in over the period",
        ["cash_out_cents", "cash_in_cents"])
def _burn(cash_out_cents, cash_in_cents):
    """cash outflows - cash inflows. Cash basis. Positive = burning."""
    return {"value_cents": int(cash_out_cents) - int(cash_in_cents), "unit": "cents"}


@metric("runway_months", "1.0", "Runway = cash balance / average monthly net burn",
        ["cash_cents", "avg_monthly_net_burn_cents"])
def _runway(cash_cents, avg_monthly_net_burn_cents):
    """cash / avg monthly net burn. Undefined (not infinite) when burn <= 0."""
    b = int(avg_monthly_net_burn_cents)
    if b <= 0:
        return {"raw": None, "unit": "months", "value_cents": None,
                "note": "net burn is zero or negative — cash-flow positive, runway undefined"}
    return {"raw": round(int(cash_cents) / b, 1), "unit": "months", "value_cents": None}


# ── working capital ──────────────────────────────────────────────────────────
@metric("dso", "1.0", "Days sales outstanding = (AR / revenue) x days in period",
        ["ar_cents", "revenue_cents", "days_in_period"])
def _dso(ar_cents, revenue_cents, days_in_period):
    """(accounts receivable / revenue) * days in period."""
    return {"raw": round((int(ar_cents) / int(revenue_cents)) * int(days_in_period), 1),
            "unit": "days", "value_cents": None}


@metric("dpo", "1.0", "Days payable outstanding = (AP / COGS) x days in period",
        ["ap_cents", "cogs_cents", "days_in_period"])
def _dpo(ap_cents, cogs_cents, days_in_period):
    """(accounts payable / COGS) * days in period."""
    return {"raw": round((int(ap_cents) / int(cogs_cents)) * int(days_in_period), 1),
            "unit": "days", "value_cents": None}


@metric("quick_ratio", "1.0", "(cash + AR) / current liabilities",
        ["cash_cents", "ar_cents", "current_liabilities_cents"])
def _qr(cash_cents, ar_cents, current_liabilities_cents):
    """(cash + accounts receivable) / current liabilities. Excludes inventory."""
    return {"raw": round((int(cash_cents) + int(ar_cents)) / int(current_liabilities_cents), 2),
            "unit": "ratio", "value_cents": None}


# ── efficiency ───────────────────────────────────────────────────────────────
@metric("cac", "1.0", "Customer acquisition cost = S&M spend / new customers",
        ["sales_marketing_cents", "new_customers"])
def _cac(sales_marketing_cents, new_customers):
    """fully loaded sales and marketing spend / new customers acquired in period"""
    return {"value_cents": int(int(sales_marketing_cents) / int(new_customers)), "unit": "cents"}


@metric("ltv_cac", "1.0", "LTV/CAC ratio", ["ltv_cents", "cac_cents"])
def _ltvcac(ltv_cents, cac_cents):
    """lifetime value / customer acquisition cost"""
    return {"raw": round(int(ltv_cents) / int(cac_cents), 2), "unit": "ratio", "value_cents": None}


@metric("variance", "1.0", "Actual vs budget, absolute and percent",
        ["actual_cents", "budget_cents"])
def _var(actual_cents, budget_cents):
    """actual - budget. Favorable/unfavorable depends on the account's sign convention."""
    a, b = int(actual_cents), int(budget_cents)
    return {"value_cents": a - b, "unit": "cents",
            "pct": money.pct(a - b, b) if b else None}
