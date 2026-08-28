"""Money is integer cents with a currency. Never a float, never a string in math.

Every rounding error this profile could ship starts with someone doing
0.1 + 0.2 in a language that thinks that is 0.30000000000000004.
"""
from __future__ import annotations
import re
from decimal import Decimal, ROUND_HALF_UP

NUM = re.compile(r"-?\$?\s?\d[\d,]*(?:\.\d+)?")


def to_cents(value, currency: str = "USD") -> int:
    if isinstance(value, int):
        return value
    s = str(value).strip().replace(",", "").replace("$", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    d = Decimal(s or "0")
    c = int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -c if neg else c


def fmt(cents: int, currency: str = "USD", parens_negative: bool = True) -> str:
    sym = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "C$", "AUD": "A$"}.get(currency, "")
    v = abs(cents) / 100.0
    s = f"{sym}{v:,.2f}"
    if cents < 0:
        return f"({s})" if parens_negative else f"-{s}"
    return s


def pct(numer: int, denom: int, places: int = 1) -> str | None:
    if not denom:
        return None
    return f"{(numer / denom) * 100:.{places}f}%"


def normalize_number_token(tok: str) -> str:
    """Canonical form for comparing a number in prose to a stored figure."""
    t = tok.strip().replace(",", "").replace("$", "").replace(" ", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").lstrip("-")
    try:
        d = Decimal(t)
    except Exception:
        return tok.strip()
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ("-" if neg else "") + str(d)


def check_currency(rows: list) -> dict:
    """Mixed-currency addition is a silent, enormous error. Catch it in code."""
    cur = {r.get("currency", "USD") for r in rows}
    return {"ok": len(cur) <= 1, "currencies": sorted(cur),
            "error": None if len(cur) <= 1 else
            f"cannot sum across currencies {sorted(cur)} without an FX policy and rate date"}
