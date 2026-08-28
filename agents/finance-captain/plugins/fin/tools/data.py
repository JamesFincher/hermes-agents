from __future__ import annotations
import datetime as dt
from ._util import tool, need_entity
from ..store import entity as E, snapshot as S, money, audit
from ..runtime import call_mcp, setting

SOURCES = {"quickbooks": "accounting", "xero": "accounting", "stripe": "payments",
           "plaid": "banking", "ramp": "spend", "gsheets": "manual", "warehouse": "sql"}


def _normalize(rows: list, source: str) -> list:
    """Everything becomes the same row shape. Amounts become integer cents."""
    out = []
    for i, r in enumerate(rows or []):
        amt = r.get("amount_cents")
        if amt is None:
            amt = money.to_cents(r.get("amount", r.get("total", 0)))
        out.append({
            "id": str(r.get("id") or r.get("txn_id") or f"{source}:{i}"),
            "date": str(r.get("date") or r.get("posted_at") or r.get("created") or "")[:10],
            "amount_cents": int(amt),
            "currency": (r.get("currency") or "USD").upper(),
            "account": r.get("account") or r.get("category") or r.get("account_name") or "",
            "vendor": r.get("vendor") or r.get("merchant") or r.get("customer") or r.get("name") or "",
            "memo": (r.get("memo") or r.get("description") or "")[:200],
            "type": r.get("type") or r.get("kind") or "",
            "source": source,
        })
    return out


@tool
def snapshot_pull(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    source = args.get("source")
    kind = args.get("kind", "transactions")
    period = args.get("period") or dt.date.today().strftime("%Y-%m")
    if source not in SOURCES:
        return {"error": f"unknown source '{source}'", "known": sorted(SOURCES)}

    env = call_mcp(source, args.get("mcp_tool", "list_transactions"),
                   {"start": args.get("start"), "end": args.get("end"),
                    "period": period, "account": args.get("account"),
                    "limit": args.get("limit", 5000)})
    if not env.get("ok"):
        return {"error": f"{source} unavailable: {env.get('error')}",
                "fallback": "export a CSV from the system and load it with "
                            "snapshot_pull source=gsheets mcp_tool=read_csv path=..., or use "
                            "scripts/load_csv.py. Never hand-type figures from a screenshot.",
                "hard_rule": "no snapshot, no numbers. Do not proceed from memory."}
    raw = env.get("result") or []
    if isinstance(raw, dict):
        raw = raw.get("rows") or raw.get("data") or raw.get("transactions") or []
    rows = _normalize(raw, source)
    cur = money.check_currency(rows)
    rec = S.create(e["entity_id"], source, kind, period, rows,
                   meta={"account": args.get("account"), "range": [args.get("start"), args.get("end")]})
    audit.write("snapshots", {"snapshot": rec["id"], "source": source, "rows": rec["rows"]})
    prior = [s for s in S.index()["snapshots"]
             if s["entity"] == e["entity_id"] and s["source"] == source
             and s["kind"] == kind and s["period"] == period and s["id"] != rec["id"]]
    out = {"ok": True, "snapshot": rec["id"], "source": source, "kind": kind,
           "period": period, "rows": rec["rows"],
           "total": money.fmt(rec["total_cents"]) if rec["total_cents"] is not None else None,
           "total_cents": rec["total_cents"], "currencies": rec["currencies"],
           "pulled_at": rec["pulled_at"],
           "note": "rows are stored, not returned. Query them with ledger_query."}
    if not cur["ok"]:
        out["currency_warning"] = cur["error"]
    if prior:
        out["prior_snapshot"] = prior[-1]["id"]
        out["restatement_check"] = f"snapshot_diff old={prior[-1]['id']} new={rec['id']}"
    return out


@tool
def snapshot_diff(args, **kw):
    d = S.diff(args["old"], args["new"], args.get("key", "id"))
    d["interpretation"] = ("restated — numbers published from the old snapshot have moved"
                           if d["restated"] else "no change since the prior pull")
    if d["restated"]:
        d["required_action"] = ("identify every published figure built on the old snapshot and "
                                "state the restatement explicitly in the next report")
    return d


@tool
def ledger_query(args, **kw):
    """Aggregate over a snapshot. Returns numbers, never raw rows unless asked."""
    e = E.load()
    if (err := need_entity(e)):
        return err
    sid = args.get("snapshot")
    rows = S.rows(sid)
    if not rows:
        return {"error": f"snapshot {sid} is empty or unknown"}

    f = args.get("filters") or {}
    def keep(r):
        if f.get("account") and f["account"].lower() not in str(r["account"]).lower():
            return False
        if f.get("vendor") and f["vendor"].lower() not in str(r["vendor"]).lower():
            return False
        if f.get("date_from") and r["date"] < f["date_from"]:
            return False
        if f.get("date_to") and r["date"] > f["date_to"]:
            return False
        if f.get("min_cents") is not None and abs(r["amount_cents"]) < int(f["min_cents"]):
            return False
        if f.get("type") and f["type"] != r["type"]:
            return False
        return True

    sel = [r for r in rows if keep(r)]
    cur = money.check_currency(sel)
    if not cur["ok"]:
        return {"error": cur["error"], "currencies": cur["currencies"]}

    group = args.get("group_by")
    total = sum(r["amount_cents"] for r in sel)
    out = {"ok": True, "snapshot": sid, "matched_rows": len(sel),
           "total_cents": total, "total": money.fmt(total)}
    if group:
        agg = {}
        for r in sel:
            k = str(r.get(group, "")) or "(blank)"
            g = agg.setdefault(k, {"count": 0, "cents": 0})
            g["count"] += 1
            g["cents"] += r["amount_cents"]
        out["groups"] = sorted(
            ({"key": k, "count": v["count"], "total_cents": v["cents"],
              "total": money.fmt(v["cents"])} for k, v in agg.items()),
            key=lambda x: -abs(x["total_cents"]))[: int(args.get("limit", 40))]
    if args.get("include_rows"):
        out["rows"] = sel[: int(args.get("limit", 25))]
        out["row_note"] = "truncated sample. Aggregate instead of listing when you can."
    return out
