#!/usr/bin/env python3
"""FX conversion with an explicit, recorded rate and date. Never an implicit rate.

  python3 fx.py --amount 125000 --from EUR --to USD --rate 1.0842 --date 2026-07-31
Rates are supplied, not guessed: pull them from your bank, your ERP, or a
published source and pass them in. This script does arithmetic, not lookup.
"""
import argparse, json
from decimal import Decimal, ROUND_HALF_UP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", required=True, help="in minor units (cents) or decimal")
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--rate", required=True, help="units of TO per one FROM")
    ap.add_argument("--date", required=True)
    ap.add_argument("--source", default="unspecified")
    a = ap.parse_args()
    amt = Decimal(str(a.amount).replace(",", "").replace("$", ""))
    if "." not in str(a.amount):
        amt = amt / 100
    rate = Decimal(a.rate)
    out = (amt * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    print(json.dumps({"from": {"currency": a.src, "amount": str(amt)},
                      "to": {"currency": a.dst, "amount": str(out),
                             "cents": int(out * 100)},
                      "rate": str(rate), "rate_date": a.date, "rate_source": a.source,
                      "disclosure": "State the rate, the date, and the source in any report "
                                    "containing this figure."}, indent=2))


if __name__ == "__main__":
    main()
