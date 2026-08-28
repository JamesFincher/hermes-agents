from __future__ import annotations
from ._util import tool
from ..store import cites, ledger as L, gates, matter as M
from ..runtime import setting
from .authority import _mcp_lookup


@tool
def cite_check(args, **kw):
    rep = gates.citation_gate(args["text"], _mcp_lookup)
    rep["verdict"] = "clean" if rep["pass"] else "blocked"
    if not rep["pass"]:
        rep["message"] = gates.block_message({"citation": rep,
                                              "fact": {"unsourced_particulars": []},
                                              "jurisdiction": {"findings": []},
                                              "currency": {"findings": []}})
    return rep


def _bluebook(a: dict, short: bool = False) -> str:
    k = a.get("kind")
    cit = a.get("citation") or ""
    title = a.get("title") or ""
    if k == "case":
        court = a.get("court") or ""
        year = (a.get("date") or "")[:4]
        if short:
            return f"{title.split(' v. ')[0]}, {cit}"
        paren = ", ".join(x for x in (court, year) if x)
        return f"{title}, {cit}" + (f" ({paren})" if paren else "")
    if k in ("statute", "regulation", "court_rule"):
        year = (a.get("as_of") or "")[:4]
        return f"{cit}" + (f" ({year})" if year else "")
    return f"{title}, {a.get('url') or cit}"


@tool
def cite_format(args, **kw):
    style = args.get("style") or setting("citation_format", "bluebook")
    ids = args.get("auth_ids")
    rows = [L.get(i) for i in ids] if ids else L.search()
    rows = [r for r in rows if r]
    if not rows:
        return {"error": "no authorities to format. Retrieve before citing."}
    fmt = [{"auth": r["id"], "cite": _bluebook(r, args.get("short_form", False)),
            "verified": r.get("verified"), "stale": L.is_stale(r)} for r in rows]
    mode = args.get("mode", "full")
    if mode == "table_of_authorities":
        buckets = {}
        for r, f in zip(rows, fmt):
            buckets.setdefault(r.get("kind", "other"), []).append(f["cite"])
        toa = {k: sorted(v) for k, v in buckets.items()}
        return {"ok": True, "style": style, "table_of_authorities": toa}
    return {"ok": True, "style": style, "citations": fmt,
            "note": "these strings are generated from retrieved records. Do not hand-edit "
                    "a citation; fix the ledger entry instead."}


@tool
def conflict_report(args, **kw):
    """Groups authorities by the proposition they were tagged with and reports
    disagreement rather than averaging it."""
    m = M.load(args.get("matter_id")) or {}
    props = {}
    for a in L.search():
        for p in a.get("propositions", []) or []:
            props.setdefault(p["text"], []).append(
                {"auth": a["id"], "citation": a.get("citation"), "stance": p.get("stance"),
                 "court": a.get("court"), "court_level": a.get("court_level"),
                 "jurisdiction": a.get("jurisdiction"), "date": a.get("date")})
    filt = args.get("proposition")
    conflicts = []
    for text, rows in props.items():
        if filt and filt.lower() not in text.lower():
            continue
        stances = {r["stance"] for r in rows}
        if len({s for s in stances if s in ("supports", "contradicts")}) > 1:
            conflicts.append({"proposition": text, "authorities": rows,
                              "in_jurisdiction": [r for r in rows
                                                  if r["jurisdiction"] == m.get("jurisdiction")]})
    return {"ok": True, "conflicts": conflicts, "count": len(conflicts),
            "instruction": "present every conflict in the work product. Do not resolve a "
                           "split by silently choosing a side."}
