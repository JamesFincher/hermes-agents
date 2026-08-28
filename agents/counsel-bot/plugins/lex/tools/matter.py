from __future__ import annotations
from ._util import tool, need_matter
from ..store import matter as M
from ..data_registry import doc_types_for_hat, hat_notes


@tool
def matter_open(args, **kw):
    action = args.get("action", "open")
    if action == "list":
        return {"ok": True, "matters": M.list_matters()}
    if action == "status":
        m = M.load(args.get("matter_id"))
        if (e := need_matter(m)):
            return e
        return {"ok": True, "matter": {k: m[k] for k in
                ("matter_id", "name", "jurisdiction", "forum", "posture", "hat",
                 "represented_party", "parties")},
                "facts_recorded": len(m.get("facts", {})),
                "issues": len(m.get("issues", [])),
                "open_questions": m.get("open_questions", []),
                "assumptions": m.get("assumptions", [])}
    if action == "switch":
        mid = args.get("matter_id")
        if not M.load(mid):
            return {"error": f"no such matter {mid}"}
        M.set_active(mid)
        return {"ok": True, "active": mid}

    missing = [k for k in ("name", "jurisdiction", "represented_party") if not args.get(k)]
    if missing:
        return {"error": f"cannot open a matter without {', '.join(missing)}. "
                         "Jurisdiction drives every authority and every gate — ask once, then proceed."}
    m = M.create(args["name"], args["jurisdiction"], args.get("forum", "none"),
                 args.get("posture", "unspecified"), args.get("parties", []),
                 args["represented_party"])
    return {"ok": True, "matter_id": m["matter_id"], "jurisdiction": m["jurisdiction"],
            "next": "set_hat, then matter_fact for everything you were actually told, then issue_plan"}


@tool
def matter_fact(args, **kw):
    m = M.load(args.get("matter_id"))
    if (e := need_matter(m)):
        return e
    action = args.get("action", "add")
    if action == "list":
        return {"ok": True, "facts": m.get("facts", {})}
    if action == "retract":
        m["facts"].pop(args.get("key", ""), None)
        M.save(m)
        return {"ok": True, "retracted": args.get("key")}
    for k in ("key", "value", "source"):
        if not args.get(k):
            return {"error": f"'{k}' is required. A fact with no source is not a fact."}
    rec = M.add_fact(m["matter_id"], args["key"], args["value"], args["source"])
    return {"ok": True, "fact": {args["key"]: rec},
            "note": "this value may now appear in drafts as a concrete particular"}


@tool
def set_hat(args, **kw):
    m = M.load(args.get("matter_id"))
    if (e := need_matter(m)):
        return e
    hat = args.get("hat")
    m["hat"] = hat
    M.save(m)
    return {"ok": True, "hat": hat,
            "document_types": doc_types_for_hat(hat),
            "load_skill": f"hat-{hat}" if hat in
                ("litigation", "transactional", "corporate", "employment", "regulatory", "pro-se")
                else "draft-document",
            "notes": hat_notes(hat)}
