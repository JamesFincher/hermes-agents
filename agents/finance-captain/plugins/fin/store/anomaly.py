"""Deterministic exception detection. No model, no judgment, no tokens.

These are the checks a controller actually runs, expressed as arithmetic.
"""
from __future__ import annotations
import re, statistics as st
from collections import Counter, defaultdict
from . import money


def duplicate_payments(rows: list, days: int = 7) -> list:
    """Same vendor, same amount, close in time — the classic double-pay."""
    buckets = defaultdict(list)
    for r in rows:
        buckets[(str(r.get("vendor", "")).lower().strip(), int(r.get("amount_cents", 0)))].append(r)
    out = []
    for (vendor, amt), group in buckets.items():
        if len(group) > 1 and amt:
            out.append({"check": "duplicate_payment", "vendor": vendor,
                        "amount": money.fmt(amt), "count": len(group),
                        "rows": [g.get("id") for g in group][:6],
                        "severity": "high"})
    return out


def outliers(rows: list, z: float = 2.5, by: str = "account") -> list:
    groups = defaultdict(list)
    for r in rows:
        groups[str(r.get(by, "unknown"))].append(r)
    out = []
    for k, g in groups.items():
        vals = [abs(int(r.get("amount_cents", 0))) for r in g]
        if len(vals) < 8:
            continue
        m, sd = st.mean(vals), st.pstdev(vals)
        if sd == 0:
            continue
        for r, v in zip(g, vals):
            score = (v - m) / sd
            if score >= z:
                out.append({"check": "outlier", by: k, "id": r.get("id"),
                            "amount": money.fmt(int(r.get("amount_cents", 0))),
                            "z": round(score, 2), "group_mean": money.fmt(int(m)),
                            "severity": "medium"})
    return out


def round_numbers(rows: list, threshold_cents: int = 100000) -> list:
    """Large, suspiciously round amounts — often estimates that became entries."""
    out = []
    for r in rows:
        a = abs(int(r.get("amount_cents", 0)))
        if a >= threshold_cents and a % 100000 == 0:
            out.append({"check": "round_number", "id": r.get("id"),
                        "amount": money.fmt(a), "severity": "low",
                        "note": "exact multiple of $1,000 at material size — confirm it is not a plug"})
    return out


def uncategorized(rows: list) -> list:
    out = []
    for r in rows:
        acct = str(r.get("account", "")).strip().lower()
        if not acct or acct in ("uncategorized", "ask my accountant", "suspense", "unknown"):
            out.append({"check": "uncategorized", "id": r.get("id"),
                        "amount": money.fmt(int(r.get("amount_cents", 0))),
                        "severity": "high",
                        "note": "cannot be reported until categorized"})
    return out


def weekend_or_backdated(rows: list) -> list:
    import datetime as dt
    out = []
    for r in rows:
        d = str(r.get("date", ""))[:10]
        try:
            day = dt.date.fromisoformat(d)
        except Exception:
            continue
        if day.weekday() >= 5:
            out.append({"check": "weekend_entry", "id": r.get("id"), "date": d,
                        "amount": money.fmt(int(r.get("amount_cents", 0))),
                        "severity": "low"})
    return out


def benford_first_digit(rows: list) -> dict:
    """Population-level shape check. Only meaningful on 300+ natural amounts."""
    digits = []
    for r in rows:
        a = abs(int(r.get("amount_cents", 0)))
        if a:
            digits.append(int(str(a)[0]))
    n = len(digits)
    if n < 300:
        return {"check": "benford", "applicable": False,
                "note": f"only {n} amounts; needs 300+ to mean anything"}
    import math
    exp = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    obs = Counter(digits)
    dev = {d: round(obs.get(d, 0) / n - exp[d], 4) for d in range(1, 10)}
    worst = max(dev.items(), key=lambda kv: abs(kv[1]))
    return {"check": "benford", "applicable": True, "n": n, "deviation": dev,
            "largest_deviation_digit": worst[0], "largest_deviation": worst[1],
            "severity": "medium" if abs(worst[1]) > 0.05 else "low",
            "note": "a shape signal only. Never an accusation, never evidence."}


def scan(rows: list, z: float = 2.5, materiality_cents: int = 100000) -> dict:
    findings = (uncategorized(rows) + duplicate_payments(rows) + outliers(rows, z)
                + round_numbers(rows, materiality_cents) + weekend_or_backdated(rows))
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: order.get(f.get("severity", "low"), 3))
    return {"rows_scanned": len(rows), "findings": findings,
            "by_severity": dict(Counter(f["severity"] for f in findings)),
            "benford": benford_first_digit(rows)}
