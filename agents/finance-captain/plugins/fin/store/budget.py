"""Budgets, forecasts, and variance. Driver-based and deterministic."""
from __future__ import annotations
import json, os, threading
from pathlib import Path
from ..runtime import data_dir
from . import money

_LOCK = threading.RLock()


def _path(entity: str) -> Path:
    return data_dir() / "entities" / f"{entity}_budget.json"


def load(entity: str) -> dict:
    p = _path(entity)
    if not p.exists():
        return {"entity": entity, "version": 1, "lines": {}, "scenarios": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"entity": entity, "version": 1, "lines": {}, "scenarios": {}}


def save(d: dict) -> None:
    p = _path(d["entity"])
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        os.replace(tmp, p)


def set_line(entity: str, period: str, account: str, amount_cents: int, note: str = "") -> dict:
    with _LOCK:
        d = load(entity)
        d["lines"].setdefault(period, {})[account] = {"amount_cents": int(amount_cents), "note": note}
        save(d)
        return d["lines"][period][account]


def variance(entity: str, period: str, actuals: dict, materiality_cents: int) -> dict:
    """actuals: {account: amount_cents}. Returns every line, flags material ones."""
    d = load(entity)
    budget = d["lines"].get(period, {})
    accounts = sorted(set(budget) | set(actuals))
    rows, material = [], []
    tot_a = tot_b = 0
    for acct in accounts:
        b = int(budget.get(acct, {}).get("amount_cents", 0))
        a = int(actuals.get(acct, 0))
        v = a - b
        tot_a += a
        tot_b += b
        row = {"account": acct, "budget_cents": b, "actual_cents": a,
               "variance_cents": v, "variance_pct": money.pct(v, b) if b else None,
               "budget": money.fmt(b), "actual": money.fmt(a), "variance": money.fmt(v),
               "material": abs(v) >= materiality_cents}
        rows.append(row)
        if row["material"]:
            material.append(row)
    return {"period": period, "rows": rows,
            "total_budget_cents": tot_b, "total_actual_cents": tot_a,
            "total_variance_cents": tot_a - tot_b,
            "material_lines": material,
            "materiality_cents": materiality_cents,
            "instruction": "every material line needs a cause, not a category name. "
                           "Unexplained material variance is an open item, not a rounding note."}


def forecast(opening_cash_cents: int, months: int, drivers: dict) -> dict:
    """Deterministic driver-based roll-forward. No model, no curve fitting.

    drivers: {"revenue_cents": [...], "cogs_pct": 0.3, "opex_cents": [...],
              "collections_lag_months": 1}
    """
    rev = [int(x) for x in drivers.get("revenue_cents", [])][:months]
    if len(rev) < months:
        rev += [rev[-1] if rev else 0] * (months - len(rev))
    opex = [int(x) for x in drivers.get("opex_cents", [])][:months]
    if len(opex) < months:
        opex += [opex[-1] if opex else 0] * (months - len(opex))
    cogs_pct = float(drivers.get("cogs_pct", 0.0))
    lag = int(drivers.get("collections_lag_months", 0))

    cash = int(opening_cash_cents)
    out = []
    for i in range(months):
        collected = rev[i - lag] if i - lag >= 0 else 0
        cogs = int(rev[i] * cogs_pct)
        net = collected - cogs - opex[i]
        cash += net
        out.append({"month": i + 1, "revenue_cents": rev[i], "collected_cents": collected,
                    "cogs_cents": cogs, "opex_cents": opex[i], "net_cents": net,
                    "ending_cash_cents": cash, "ending_cash": money.fmt(cash)})
    negative = next((r["month"] for r in out if r["ending_cash_cents"] < 0), None)
    return {"months": out, "cash_goes_negative_month": negative,
            "assumptions": drivers,
            "caveat": "point estimate from stated drivers. Not a prediction. "
                      "Run the downside scenario before anyone acts on this."}
