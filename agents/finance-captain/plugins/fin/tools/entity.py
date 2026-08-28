from __future__ import annotations
from ._util import tool, need_entity
from ..store import entity as E
from ..data_registry import reports_for_hat, hats


@tool
def entity_open(args, **kw):
    action = args.get("action", "open")
    if action == "status":
        e = E.load(args.get("entity_id"))
        if (err := need_entity(e)):
            return err
        return {"ok": True, "entity": {k: e.get(k) for k in
                ("entity_id", "name", "home_currency", "basis", "fiscal_year_end", "hat", "systems")},
                "periods": e.get("periods", {}),
                "open_items": e.get("open_items", []),
                "assumptions": e.get("assumptions", [])}
    if action == "switch":
        if not E.load(args.get("entity_id")):
            return {"error": f"no such entity {args.get('entity_id')}"}
        E.set_active(args["entity_id"])
        return {"ok": True, "active": args["entity_id"]}
    if action == "set_hat":
        e = E.load()
        if (err := need_entity(e)):
            return err
        e["hat"] = args.get("hat")
        E.save(e)
        return {"ok": True, "hat": e["hat"], "reports": reports_for_hat(e["hat"]),
                "load_skill": f"hat-{e['hat']}", "notes": hats().get(e["hat"], {})}

    missing = [k for k in ("name", "home_currency", "basis") if not args.get(k)]
    if missing:
        return {"error": f"cannot open an entity without {', '.join(missing)}",
                "note": "basis must be 'cash' or 'accrual' — every number downstream means "
                        "something different depending on which, and mixing them silently is "
                        "the most common reporting error there is."}
    if args["basis"] not in ("cash", "accrual"):
        return {"error": "basis must be 'cash' or 'accrual'"}
    e = E.create(args["name"], args["home_currency"], args.get("fiscal_year_end", "12-31"),
                 args["basis"], args.get("systems", {}), args.get("hat"))
    return {"ok": True, "entity_id": e["entity_id"], "basis": e["basis"],
            "next": "entity_open action=set_hat, then snapshot_pull per connected system"}


@tool
def period_manage(args, **kw):
    e = E.load()
    if (err := need_entity(e)):
        return err
    eid, p = e["entity_id"], args.get("period")
    action = args.get("action", "status")
    if action == "status":
        if p:
            st = E.period(eid, p)
            done = [k for k, v in st.get("checklist", {}).items() if v]
            return {"ok": True, "period": p, "status": st.get("status"),
                    "checklist_done": done,
                    "checklist_remaining": [c for c in E.CLOSE_CHECKLIST if c not in done]}
        return {"ok": True, "periods": e.get("periods", {}), "checklist": E.CLOSE_CHECKLIST}
    if not p:
        return {"error": "period required, e.g. '2026-07'"}
    if action == "check":
        item = args.get("item")
        if item not in E.CLOSE_CHECKLIST:
            return {"error": f"unknown checklist item", "valid": E.CLOSE_CHECKLIST}
        st = E.period(eid, p)
        st.setdefault("checklist", {})[item] = bool(args.get("done", True))
        E.set_period(eid, p, st)
        remaining = [c for c in E.CLOSE_CHECKLIST if not st["checklist"].get(c)]
        return {"ok": True, "period": p, "item": item, "remaining": remaining}
    if action == "close":
        st = E.period(eid, p)
        remaining = [c for c in E.CLOSE_CHECKLIST if not st.get("checklist", {}).get(c)]
        if remaining and not args.get("force"):
            return {"error": "close checklist incomplete", "remaining": remaining,
                    "note": "pass force=true only with a written reason; it is recorded."}
        E.set_period(eid, p, {"status": "closed", "closed_at": __import__("datetime")
                              .datetime.now().isoformat(),
                              "forced": bool(args.get("force")),
                              "force_reason": args.get("reason")})
        return {"ok": True, "period": p, "status": "closed", "forced": bool(args.get("force"))}
    if action == "reopen":
        if not args.get("reason"):
            return {"error": "reopening a closed period requires a reason; it is recorded "
                             "and any report built on the closed numbers may be restated."}
        E.set_period(eid, p, {"status": "open", "reopen_reason": args["reason"]})
        return {"ok": True, "period": p, "status": "open",
                "warning": "run snapshot_diff against prior pulls before republishing anything"}
    return {"error": f"unknown action {action}"}
