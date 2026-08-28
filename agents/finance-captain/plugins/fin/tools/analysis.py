from __future__ import annotations
import datetime as dt
from ._util import tool, need_entity
from ..store import (entity as E, snapshot as S, figures as F, metrics as MET,
                     budget as B, anomaly, money, gates)
from ..runtime import setting


@tool
def metric_registry(args, **kw):
    reg = MET.registry()
    name = args.get("metric")
    if name:
        spec = reg.get(name)
        return {"ok": True, "metric": spec} if spec else {"error": f"unknown metric '{name}'",
                                                          "available": sorted(reg)}
    return {"ok": True, "metrics": reg,
            "rule": "these definitions are the only ones this entity uses. If a stakeholder "
                    "means something different by a metric, that is a definition change with a "
                    "version bump, not a one-off recalculation."}


@tool
def metric_compute(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    name = args["metric"]
    res = MET.compute(name, args.get("inputs", {}))
    if "error" in res:
        return res
    fig = F.record(label=f"{name} ({args.get('period','')})",
                   value_cents=res.get("value_cents"), formula=res["formula"],
                   inputs={**res["inputs"], "metric_version": res["version"]},
                   snapshot_ids=args.get("snapshots", []),
                   period=args.get("period", ""), entity=e["entity_id"],
                   currency=e.get("home_currency", "USD"),
                   unit=res.get("unit", "cents"), raw=res.get("raw"))
    return {"ok": True, "figure": fig["id"], "metric": name, "version": res["version"],
            "value": fig["formatted"], "value_cents": res.get("value_cents"),
            "raw": res.get("raw"), "pct": res.get("pct"), "note": res.get("note"),
            "formula": res["formula"], "inputs": res["inputs"],
            "cite_as": f"[{fig['id']}]",
            "rule": "quote this number only with its [F#] tag. The number fence checks both."}


@tool
def budget_manage(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    action = args.get("action", "get")
    eid = e["entity_id"]
    if action == "get":
        d = B.load(eid)
        return {"ok": True, "periods": sorted(d["lines"]), "lines": d["lines"].get(args.get("period"), {})}
    if action == "set":
        for ln in args.get("lines", []):
            B.set_line(eid, args["period"], ln["account"],
                       money.to_cents(ln.get("amount", ln.get("amount_cents", 0))), ln.get("note", ""))
        return {"ok": True, "period": args["period"],
                "lines": len(args.get("lines", []))}
    return {"error": f"unknown action {action}"}


@tool
def variance_report(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    mat = int(args.get("materiality_cents") or setting("materiality_cents", 100000))
    actuals = {}
    if args.get("snapshot"):
        rows = S.rows(args["snapshot"])
        for r in rows:
            actuals[r["account"] or "(blank)"] = actuals.get(r["account"] or "(blank)", 0) + r["amount_cents"]
    actuals.update({k: money.to_cents(v) for k, v in (args.get("actuals") or {}).items()})
    v = B.variance(e["entity_id"], args["period"], actuals, mat)
    figs = []
    for row in v["material_lines"]:
        f = F.record(label=f"variance {row['account']} {args['period']}",
                     value_cents=row["variance_cents"],
                     formula="actual - budget", inputs={"actual_cents": row["actual_cents"],
                                                        "budget_cents": row["budget_cents"]},
                     snapshot_ids=[args["snapshot"]] if args.get("snapshot") else [],
                     period=args["period"], entity=e["entity_id"],
                     currency=e.get("home_currency", "USD"))
        row["figure"] = f["id"]
        figs.append(f["id"])
    v["figures"] = figs
    v["ok"] = True
    return v


@tool
def cash_forecast(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    opening = money.to_cents(args.get("opening_cash", args.get("opening_cash_cents", 0)))
    res = B.forecast(opening, int(args.get("months", 12)), args.get("drivers", {}))
    f = F.record(label=f"ending cash month {len(res['months'])}",
                 value_cents=res["months"][-1]["ending_cash_cents"] if res["months"] else 0,
                 formula="driver roll-forward: opening + collections - COGS - opex",
                 inputs={"opening_cash_cents": opening, **args.get("drivers", {})},
                 snapshot_ids=args.get("snapshots", []), period=args.get("period", ""),
                 entity=e["entity_id"], currency=e.get("home_currency", "USD"))
    res["ending_cash_figure"] = f["id"]
    res["ok"] = True
    if res["cash_goes_negative_month"]:
        res["ALERT"] = (f"cash goes negative in month {res['cash_goes_negative_month']} "
                        "on these assumptions. Say this first, before anything else in the report.")
    return res


@tool
def anomaly_scan(args, **kw):
    rows = S.rows(args["snapshot"])
    if not rows:
        return {"error": f"snapshot {args.get('snapshot')} is empty or unknown"}
    res = anomaly.scan(rows, float(args.get("z") or setting("anomaly_z", 2.5)),
                       int(args.get("materiality_cents") or setting("materiality_cents", 100000)))
    res["ok"] = True
    res["instruction"] = ("these are deterministic exceptions, not conclusions. Each one is a "
                          "question for a human, and none of them is an accusation.")
    return res


@tool
def recon_tieout(args, **kw):
    """Two-source reconciliation: books vs bank, or report totals vs a snapshot."""
    if args.get("report_totals") and args.get("snapshot"):
        return gates.tieout({k: money.to_cents(v) for k, v in args["report_totals"].items()},
                            args["snapshot"], args.get("tolerance_cents"))
    a, b = args.get("snapshot_a"), args.get("snapshot_b")
    ra, rb = S.rows(a), S.rows(b)
    if not ra or not rb:
        return {"error": "need two populated snapshots, or report_totals + snapshot"}
    ta = sum(r["amount_cents"] for r in ra)
    tb = sum(r["amount_cents"] for r in rb)
    tol = int(args.get("tolerance_cents") or setting("tieout_tolerance_cents", 100))
    # unmatched items by (date, amount)
    ka = {(r["date"], r["amount_cents"]) for r in ra}
    kb = {(r["date"], r["amount_cents"]) for r in rb}
    only_a = [r for r in ra if (r["date"], r["amount_cents"]) not in kb]
    only_b = [r for r in rb if (r["date"], r["amount_cents"]) not in ka]
    return {"ok": True, "a": a, "b": b,
            "total_a": money.fmt(ta), "total_b": money.fmt(tb),
            "delta": money.fmt(ta - tb), "delta_cents": ta - tb,
            "ties": abs(ta - tb) <= tol, "tolerance_cents": tol,
            "in_a_not_b": only_a[:20], "in_b_not_a": only_b[:20],
            "counts": {"in_a_not_b": len(only_a), "in_b_not_a": len(only_b)},
            "rule": "an unexplained difference is an open item. Never a plug entry."}
