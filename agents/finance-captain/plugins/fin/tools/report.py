from __future__ import annotations
from pathlib import Path
from ._util import tool, need_entity
from ..store import entity as E, gates, figures as F, snapshot as S, money
from ..data_registry import report_types, reports_for_hat


@tool
def report_scaffold(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    hat = e.get("hat")
    key = args.get("report_type")
    allowed = reports_for_hat(hat) if hat else sorted(report_types())
    if key in ("?", "list", "", None):
        return {"ok": True, "hat": hat, "report_types": allowed}
    spec = report_types().get(key)
    if not spec:
        return {"error": f"unknown report type '{key}'", "available": allowed,
                "note": "add it to plugins/fin/data/report_types.json with its required "
                        "sections and required figures. Do not improvise a report structure."}
    period = args.get("period", "")
    have = {f["label"]: f["id"] for f in F.by_period(e["entity_id"], period)}
    sections = []
    for s in spec["sections"]:
        sections.append({"heading": s["heading"], "purpose": s.get("purpose"),
                         "required": s.get("required", True),
                         "figures_required": s.get("figures", []),
                         "must_tie": s.get("must_tie", False)})
    return {"ok": True, "report_type": key, "period": period, "hat": hat,
            "basis": e.get("basis"), "currency": e.get("home_currency"),
            "sections": sections,
            "required_metrics": spec.get("metrics", []),
            "figures_available": have,
            "tie_out": spec.get("tie_out"),
            "rule": "every number you write needs a [F#]. Compute first, write second. "
                    "Anything you cannot compute is [[EST: basis]] or [[TBD: what is missing]].",
            "next": "report_check before writing to disk"}


@tool
def report_check(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    text = args.get("text")
    if not text and args.get("path"):
        p = Path(args["path"])
        if not p.exists():
            return {"error": f"no file at {args['path']}"}
        text = p.read_text(encoding="utf-8", errors="replace")
    if not text:
        return {"error": "pass text or path"}
    period = args.get("period", "")
    closed = E.is_closed(e["entity_id"], period) if period else False
    totals = {k: money.to_cents(v) for k, v in (args.get("report_totals") or {}).items()}
    rep = gates.run_all(text, args.get("snapshots", []), totals or None,
                        args.get("tie_to"), bool(args.get("final")), closed)
    if args.get("report_type"):
        spec = report_types().get(args["report_type"], {})
        missing = [s["heading"] for s in spec.get("sections", [])
                   if s.get("required", True) and s["heading"].lower() not in text.lower()]
        rep["required_sections"] = {"missing": missing, "pass": not missing}
        if missing:
            rep["blocking"].append("sections")
            rep["pass"] = False
    rep["period_closed"] = closed
    rep["verdict"] = "clean" if rep["pass"] else "blocked"
    if not rep["pass"]:
        rep["message"] = gates.block_message(rep)
    elif not closed and period:
        rep["label_required"] = "PRELIMINARY — period not closed"
    return rep


@tool
def figure_check(args, **kw):
    """Look up a figure, or list what backs a period."""
    if args.get("figure"):
        f = F.get(args["figure"])
        return {"ok": True, "figure": f} if f else {"error": f"no figure {args['figure']}"}
    e = E.load()
    if (err := need_entity(e)):
        return err
    figs = F.by_period(e["entity_id"], args.get("period", ""))
    return {"ok": True, "count": len(figs),
            "figures": [{"id": f["id"], "label": f["label"], "value": f["formatted"],
                         "snapshots": f["snapshots"], "computed_at": f["computed_at"]}
                        for f in figs]}


@tool
def audit_trail(args, **kw):
    from ..store import audit
    stream = args.get("stream", "policy")
    return {"ok": True, "stream": stream, "entries": audit.tail(stream, int(args.get("n", 50)))}
