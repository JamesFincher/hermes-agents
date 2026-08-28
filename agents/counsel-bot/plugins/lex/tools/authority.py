from __future__ import annotations
import datetime as dt
from ._util import tool, need_matter
from ..store import ledger as L, bus, matter as M
from ..runtime import call_mcp, setting


def _mcp_lookup(citation: str) -> dict:
    """CourtListener citation-lookup: the anti-hallucination service.
    Returns {ok, found, title, url}."""
    env = call_mcp("courtlistener", "citation-lookup", {"text": citation})
    if not env.get("ok"):
        return {"ok": False, "error": env.get("error")}
    res = env.get("result") or []
    if isinstance(res, dict):
        res = res.get("results", []) or [res]
    for r in res:
        if str(r.get("status")) == "200" and r.get("clusters"):
            c = r["clusters"][0]
            return {"ok": True, "found": True,
                    "title": c.get("case_name"), "url": c.get("absolute_url"),
                    "date": c.get("date_filed"), "court": c.get("court")}
    return {"ok": True, "found": False}


@tool
def authority_search(args, **kw):
    m = M.load()
    juris = args.get("jurisdiction") or (m or {}).get("jurisdiction")
    if not juris:
        return {"error": "no jurisdiction: open a matter or pass jurisdiction explicitly"}
    kind = args.get("kind", "any")
    q = args["query"]
    limit = min(int(args.get("limit", 8)), 25)

    local = [L.card(a) for a in L.search(q, kind, juris)][:limit]
    remote, source = [], None
    server = {"case": "courtlistener", "court_rule": "courtlistener",
              "regulation": "ecfr", "statute": "govinfo"}.get(kind, "courtlistener")
    env = call_mcp(server, "search", {"q": q, "jurisdiction": juris,
                                      "court": args.get("court"),
                                      "date_after": args.get("date_after"),
                                      "date_before": args.get("date_before"),
                                      "limit": limit})
    if env.get("ok"):
        source = server
        for r in (env.get("result") or [])[:limit]:
            row = L.add({"kind": kind if kind != "any" else "case",
                         "citation": r.get("citation"), "title": r.get("title") or r.get("case_name"),
                         "url": r.get("url") or r.get("absolute_url"),
                         "jurisdiction": r.get("jurisdiction") or juris,
                         "court": r.get("court"), "date": r.get("date") or r.get("date_filed"),
                         "origin": f"mcp:{server}", "verified": True, "tier": "A",
                         "matter_id": (m or {}).get("matter_id")},
                        text=r.get("text") or r.get("plain_text"))
            remote.append(L.card(row))
    return {"ok": True, "jurisdiction": juris, "source": source or "ledger-only",
            "mcp_error": None if env.get("ok") else env.get("error"),
            "from_ledger": local, "retrieved": remote,
            "note": "cards only. Use authority_read for text; never quote from a card alone."}


@tool
def authority_add(args, **kw):
    m = M.load()
    text = args.get("text")
    if not text and args.get("path"):
        try:
            from pathlib import Path
            p = Path(args["path"])
            text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else None
        except Exception as e:
            return {"error": f"could not read {args['path']}: {e}"}
    row = L.add({k: args.get(k) for k in
                 ("kind", "citation", "title", "url", "jurisdiction", "court", "date", "as_of")}
                | {"origin": "manual", "matter_id": (m or {}).get("matter_id"),
                   "tier": "A" if args.get("kind") in ("case", "statute", "regulation", "court_rule") else "C"},
                text=text)
    return {"ok": True, "card": L.card(row),
            "warning": None if text else "registered without full text — "
                       "quote-span verification is unavailable until the text is stored"}


@tool
def authority_read(args, **kw):
    a = L.get(args["auth_id"])
    if not a:
        return {"error": f"no authority {args['auth_id']}"}
    if not a.get("sha"):
        return {"error": f"{a['id']} has no stored text. Re-retrieve it before quoting."}
    r = bus.read(a["sha"], int(args.get("offset", 0)),
                 min(int(args.get("limit", 4000)), 20000), args.get("find"))
    r["auth"] = a["id"]
    r["citation"] = a.get("citation")
    return r


@tool
def authority_status(args, **kw):
    a = L.get(args["auth_id"])
    if not a:
        return {"error": f"no authority {args['auth_id']}"}
    out = {"auth": a["id"], "citation": a.get("citation"), "kind": a.get("kind"),
           "as_of": a.get("as_of"), "stale": L.is_stale(a), "verified": a.get("verified")}
    if a.get("kind") == "case" and (args.get("refresh") or not a.get("treatment", {}).get("checked")):
        env = call_mcp("courtlistener", "opinions-cited", {"cited_opinion": a.get("citation")})
        if env.get("ok"):
            res = env.get("result") or []
            n = len(res) if isinstance(res, list) else res.get("count", 0)
            treat = {"checked": True, "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "citing_count": n,
                     "summary": f"{n} citing opinions found",
                     "limitation": "citation counts are not a validity signal. This is NOT "
                                   "Shepard's or KeyCite. Negative treatment must be read, "
                                   "not inferred from a count."}
        else:
            treat = {"checked": False, "error": env.get("error"),
                     "summary": "treatment check unavailable"}
        L.update(a["id"], {"treatment": treat})
        out["treatment"] = treat
    else:
        out["treatment"] = a.get("treatment", {"checked": False})
    if L.is_stale(a):
        out["required_action"] = "re-retrieve before this authority may be cited"
    return out
