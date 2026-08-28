from __future__ import annotations
from pathlib import Path
from ._util import tool, need_matter
from ..store import matter as M, gates, ledger as L, rules
from ..data_registry import doc_spec, doc_types_for_hat
from ..runtime import setting
from .authority import _mcp_lookup


@tool
def draft_scaffold(args, **kw):
    m = M.load(args.get("matter_id"))
    if (e := need_matter(m)):
        return e
    hat = m.get("hat")
    if not hat:
        return {"error": "set_hat first — the hat decides which documents exist and what they require"}
    dt_key = args.get("doc_type")
    allowed = doc_types_for_hat(hat)
    if dt_key in ("?", "list", ""):
        return {"ok": True, "hat": hat, "document_types": allowed}
    spec = doc_spec(dt_key)
    if not spec:
        return {"error": f"unknown document type '{dt_key}'", "available_for_hat": allowed,
                "note": "if this document genuinely exists and is missing, add it to "
                        "plugins/lex/data/doc_types.json with its required elements — "
                        "do not improvise a structure."}
    if hat not in spec.get("hats", []):
        return {"error": f"'{dt_key}' is not a {hat} document", "available_for_hat": allowed}

    facts = m.get("facts", {})
    sections = []
    for s in spec.get("sections", []):
        slots = []
        for slot in s.get("slots", []):
            if slot in facts:
                slots.append({"slot": slot, "value": facts[slot]["value"], "source": facts[slot]["source"]})
            else:
                slots.append({"slot": slot, "value": f"[[FACT:{slot}|{s.get('slot_help', {}).get(slot, 'needed')}]]",
                              "source": None})
        sections.append({"heading": s["heading"], "required": s.get("required", True),
                         "purpose": s.get("purpose"), "slots": slots,
                         "authority_required": s.get("authority_required", False)})
    return {"ok": True, "doc_type": dt_key, "hat": hat,
            "jurisdiction": m["jurisdiction"], "forum": m.get("forum"),
            "sections": sections,
            "authority_needed": spec.get("authority_needed", []),
            "formatting": spec.get("formatting", {}),
            "missing_facts": [sl["slot"] for s in sections for sl in s["slots"] if sl["source"] is None],
            "rule": "every [[FACT:...]] placeholder stays a placeholder until matter_fact "
                    "records a real value. Do not fill them from inference.",
            "next": "draft the text, then draft_check before writing to disk"}


@tool
def draft_check(args, **kw):
    text = args.get("text")
    if not text and args.get("path"):
        p = Path(args["path"])
        if not p.exists():
            return {"error": f"no file at {args['path']}"}
        text = p.read_text(encoding="utf-8", errors="replace")
    if not text:
        return {"error": "pass text or path"}
    m = M.load()
    rep = gates.run_all(text, (m or {}).get("matter_id"), _mcp_lookup)

    if args.get("doc_type"):
        spec = doc_spec(args["doc_type"]) or {}
        missing = [s["heading"] for s in spec.get("sections", [])
                   if s.get("required", True) and s["heading"].lower() not in text.lower()]
        rep["required_elements"] = {"missing": missing, "pass": not missing}
        if missing:
            rep["blocking"].append("elements")
            rep["pass"] = False
    rep["verdict"] = "clean" if rep["pass"] else "blocked"
    if not rep["pass"]:
        rep["message"] = gates.block_message(rep)
    return rep


@tool
def deadline_compute(args, **kw):
    if not setting("allow_deadline_without_rule", False):
        a = L.get(args.get("rule_auth_id", ""))
        if not a:
            return {"error": "no such rule authority. A deadline is never computed from memory: "
                             "retrieve the rule that supplies the period, then pass its auth id.",
                    "how": "authority_search kind=court_rule query='<rule number>'"}
        if a.get("kind") not in ("court_rule", "statute", "regulation"):
            return {"error": f"{a['id']} is a {a.get('kind')}, not a rule/statute/regulation"}
        if L.is_stale(a):
            return {"error": f"{a['id']} is stale (as of {a.get('as_of')}). Re-retrieve it first."}
    try:
        r = rules.compute(args["trigger_date"], int(args["period_days"]),
                          args.get("day_type", "calendar"), args.get("direction", "after"))
    except ValueError as e:
        return {"error": f"bad date input: {e}"}
    r["rule_auth"] = args.get("rule_auth_id")
    r["verify"] = ("Confirm against the forum's own calendar and local rules before relying "
                   "on this date. This computation knows federal holidays only.")
    return {"ok": True, **r}
