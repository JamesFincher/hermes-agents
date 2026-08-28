"""Citation extraction and verification.

Two layers, and the order matters:
  1. Local extraction (eyecite if installed, regex fallback). Finds every
     citation-shaped string in the text, including ones the model invented.
  2. Resolution against the ledger, then against the CourtListener
     citation-lookup service via the plugin's MCP facade.

A citation that cannot be resolved to a document we actually retrieved is
reported unresolved. The gate turns that into a block.
"""
from __future__ import annotations
import re

# Reporter-shaped: <volume> <reporter> <page>  e.g. 576 U.S. 644, 143 S. Ct. 2298
CASE_RE = re.compile(
    r"\b(\d{1,4})\s+([A-Z][A-Za-z.'’]*(?:\s*[A-Z][A-Za-z.'’]*){0,4}\.?(?:\s?\d[dh]?)?)\s+(\d{1,5})\b")
# Federal statute / CFR: 17 U.S.C. § 107 ; 29 C.F.R. § 785.11
CODE_RE = re.compile(r"\b(\d{1,2})\s+(U\.?S\.?C\.?|C\.?F\.?R\.?)\s*§+\s*([\w.\-()]+)")
# State code-ish: Cal. Civ. Code § 1542 ; N.Y. Gen. Oblig. Law § 5-1401
STATE_RE = re.compile(r"\b([A-Z][A-Za-z.]{1,6}(?:\s+[A-Z][A-Za-z.]{1,12}){0,4})\s+(?:Code|Law|Stat\.?|Rev\. Stat\.?)\s*§+\s*([\w.\-()]+)")
RULE_RE = re.compile(r"\b(Fed\.?\s?R\.?\s?(?:Civ|Crim|App|Evid|Bankr)\.?\s?P\.?|F\.?R\.?C\.?P\.?)\s*\.?\s*([\d.()a-zA-Z\-]+)")


def extract(text: str) -> list:
    """Returns [{raw, kind, start, end}]. Prefers eyecite when available."""
    try:
        from eyecite import get_citations  # type: ignore
        out = []
        for c in get_citations(text):
            raw = getattr(c, "matched_text", lambda: str(c))()
            span = getattr(c, "span", lambda: (0, 0))()
            out.append({"raw": raw, "kind": type(c).__name__, "start": span[0], "end": span[1],
                        "engine": "eyecite"})
        if out:
            return out
    except Exception:
        pass

    out, seen = [], set()
    for rx, kind in ((CODE_RE, "statute"), (STATE_RE, "statute"),
                     (RULE_RE, "court_rule"), (CASE_RE, "case")):
        for m in rx.finditer(text):
            raw = m.group(0).strip()
            key = (raw.lower(), m.start())
            if key in seen:
                continue
            seen.add(key)
            out.append({"raw": raw, "kind": kind, "start": m.start(), "end": m.end(),
                        "engine": "regex"})
    return sorted(out, key=lambda x: x["start"])


def normalize(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip().rstrip(",.;")


def resolve(raw: str, ledger_mod, mcp_lookup=None) -> dict:
    """ledger first (we retrieved it), then the lookup service, else unresolved."""
    n = normalize(raw)
    hit = ledger_mod.find_citation(n)
    if hit:
        return {"citation": n, "status": "in_ledger", "auth": hit["id"],
                "verified": bool(hit.get("verified")), "title": hit.get("title")}
    if mcp_lookup:
        try:
            r = mcp_lookup(n)
            if r.get("ok") and r.get("found"):
                return {"citation": n, "status": "exists_not_retrieved",
                        "title": r.get("title"), "url": r.get("url"),
                        "note": "real citation, but not retrieved into this matter — retrieve before relying on it"}
            if r.get("ok"):
                return {"citation": n, "status": "not_found",
                        "note": "lookup service returned no match for this reporter/volume/page"}
        except Exception:
            pass
    return {"citation": n, "status": "unresolved",
            "note": "not in the ledger and no lookup available — cannot be used"}
