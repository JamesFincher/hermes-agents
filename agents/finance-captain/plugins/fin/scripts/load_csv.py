#!/usr/bin/env python3
"""Load a CSV/XLSX export into a fin snapshot without it ever touching context.

  python3 load_csv.py bank.csv --entity E260827 --source plaid --kind transactions \
      --period 2026-07 --map date=Date,amount=Amount,vendor=Description
Prints the snapshot record as JSON.
"""
import argparse, csv, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from fin.store import snapshot as S, money  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--entity", required=True)
    ap.add_argument("--source", default="gsheets"); ap.add_argument("--kind", default="transactions")
    ap.add_argument("--period", required=True)
    ap.add_argument("--map", default="", help="target=Column,target=Column")
    ap.add_argument("--currency", default="USD")
    a = ap.parse_args()
    m = dict(kv.split("=", 1) for kv in a.map.split(",") if "=" in kv)
    rows = []
    with open(a.path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for i, r in enumerate(csv.DictReader(f)):
            g = lambda k, d="": r.get(m.get(k, k), r.get(k, d)) or d
            rows.append({"id": g("id", f"csv:{i}"), "date": str(g("date"))[:10],
                         "amount_cents": money.to_cents(g("amount", "0")),
                         "currency": (g("currency", a.currency) or a.currency).upper(),
                         "account": g("account"), "vendor": g("vendor"),
                         "memo": g("memo")[:200], "type": g("type"), "source": a.source})
    rec = S.create(a.entity, a.source, a.kind, a.period, rows, meta={"file": os.path.basename(a.path)})
    print(json.dumps({**rec, "total": money.fmt(rec["total_cents"]) if rec["total_cents"] is not None else None}, indent=2))


if __name__ == "__main__":
    main()
