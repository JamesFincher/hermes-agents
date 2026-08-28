"""The gates. This module is the reason the profile exists.

Four deterministic checks run over any draft before it can be written:

  CITATION GATE  every citation-shaped string resolves to an authority we
                 actually retrieved. Unresolvable → block.
  FACT FENCE     every concrete particular (name, date, money, address,
                 docket, duration) traces to the matter fact table or is an
                 explicit [[FACT:...]] placeholder. Invented particular → block.
  JURISDICTION   an authority from outside the matter's jurisdiction may not be
                 described in binding language. Mismatch → block.
  CURRENCY       statutes/regs/rules cited must be inside the staleness window
                 and cases must have had a treatment check attempted.

Every check returns findings with the offending text quoted, so the model can
fix precisely rather than regenerate blindly.
"""
from __future__ import annotations
import re
from . import cites, ledger, matter
from ..runtime import setting

PLACEHOLDER = re.compile(r"\[\[FACT:[^\]]+\]\]")
BINDING_WORDS = re.compile(
    r"(?i)\b(binding|controls|controlling|requires that|mandates|is dispositive|"
    r"the court must|settled law in this (?:state|circuit|district))\b")

# Concrete particulars a drafter must never invent.
MONEY = re.compile(r"\$\s?[\d,]+(?:\.\d{2})?")
DATE = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
                  r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
                  r"Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
DOCKET = re.compile(r"\b(?:No\.|Case No\.|Docket No\.)\s*[\dA-Za-z:\-]{4,}")
ADDRESS = re.compile(r"\b\d{1,6}\s+[A-Z][A-Za-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Ct|Court)\b\.?")
DURATION = re.compile(r"\b(?:within|no later than|for a (?:term|period) of)\s+(?:\d{1,4}|[a-z\-]+)\s+"
                      r"(?:calendar |business |court )?(?:days?|months?|years?)\b", re.I)
PARTYISH = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}),?\s+(?:Inc\.|LLC|L\.L\.C\.|Corp\.|Ltd\.|LP|PLLC)\b")

# Words that make a sentence a legal assertion needing authority.
ASSERTION = re.compile(
    r"(?i)\b(is required|must|shall be liable|the elements are|courts have held|"
    r"the standard is|is unlawful|is prohibited|statute of limitations|is preempted|"
    r"the law (?:in|of)|entitles?|constitutes)\b")

SAFE_CONTEXT = re.compile(r"(?i)\b(example|illustrat|hypothetical|sample|e\.g\.)\b")


def _mask(text: str) -> str:
    """Remove placeholders and citations before hunting for invented particulars."""
    t = PLACEHOLDER.sub(" ", text)
    for c in cites.extract(text):
        t = t.replace(c["raw"], " ")
    return t


def _sentences(text: str):
    for s in re.split(r"(?<=[.;:])\s+|\n{2,}", text):
        s = s.strip()
        if s:
            yield s


def citation_gate(text: str, mcp_lookup=None) -> dict:
    found = cites.extract(text)
    results, blocking = [], []
    for c in found:
        r = cites.resolve(c["raw"], ledger, mcp_lookup)
        r["offset"] = c["start"]
        results.append(r)
        if r["status"] in ("unresolved", "not_found", "exists_not_retrieved"):
            blocking.append(r)
    # A legal assertion with no citation anywhere in its sentence is also a finding.
    uncited = []
    for s in _sentences(text):
        if ASSERTION.search(s) and not cites.extract(s) and not SAFE_CONTEXT.search(s):
            uncited.append(s[:220])
    return {"citations": results, "unresolved": blocking,
            "uncited_assertions": uncited,
            "pass": not blocking and not uncited}


def fact_fence(text: str, matter_id: str | None = None) -> dict:
    known = matter.fact_values(matter_id)
    masked = _mask(text)
    findings = []
    for label, rx in (("money", MONEY), ("date", DATE), ("docket", DOCKET),
                      ("address", ADDRESS), ("duration", DURATION), ("entity", PARTYISH)):
        for m in rx.finditer(masked):
            raw = m.group(0).strip()
            if any(raw in k or k in raw for k in known):
                continue
            findings.append({"kind": label, "text": raw, "offset": m.start(),
                             "fix": f"replace with [[FACT:{label}_...|describe what is needed]] "
                                    f"or record it via matter_fact"})
    return {"unsourced_particulars": findings,
            "placeholders": len(PLACEHOLDER.findall(text)),
            "pass": not findings}


def jurisdiction_fence(text: str, matter_id: str | None = None) -> dict:
    m = matter.load(matter_id) or {}
    juris = m.get("jurisdiction")
    if not juris:
        return {"pass": False, "findings": [{"issue": "no jurisdiction on the matter — "
                                             "run matter_open before drafting"}]}
    findings = []
    for c in cites.extract(text):
        a = ledger.find_citation(cites.normalize(c["raw"]))
        if not a:
            continue
        aj = a.get("jurisdiction")
        if aj and aj != juris and aj != "US-FED":
            window = text[max(0, c["start"] - 260): c["end"] + 260]
            if BINDING_WORDS.search(window):
                findings.append({"auth": a["id"], "citation": a.get("citation"),
                                 "authority_jurisdiction": aj, "matter_jurisdiction": juris,
                                 "issue": "out-of-jurisdiction authority framed as binding",
                                 "fix": "relabel as persuasive, or find in-jurisdiction authority"})
    return {"jurisdiction": juris, "findings": findings, "pass": not findings}


def currency_gate(text: str) -> dict:
    findings = []
    require_treatment = bool(setting("require_treatment_check", True))
    for c in cites.extract(text):
        a = ledger.find_citation(cites.normalize(c["raw"]))
        if not a:
            continue
        if ledger.is_stale(a):
            findings.append({"auth": a["id"], "citation": a.get("citation"),
                             "issue": f"as-of {a.get('as_of')} is outside the staleness window",
                             "fix": "re-retrieve before relying on it"})
        if a.get("kind") == "case" and require_treatment and not a.get("treatment", {}).get("checked"):
            findings.append({"auth": a["id"], "citation": a.get("citation"),
                             "issue": "no treatment check attempted",
                             "fix": "authority_status auth_id=" + a["id"]})
    return {"findings": findings, "pass": not findings}


def run_all(text: str, matter_id: str | None = None, mcp_lookup=None) -> dict:
    cg = citation_gate(text, mcp_lookup)
    ff = fact_fence(text, matter_id)
    jf = jurisdiction_fence(text, matter_id)
    cu = currency_gate(text)
    strict_c = str(setting("citation_gate", "strict")) == "strict"
    strict_f = str(setting("fact_fence", "strict")) == "strict"
    blocking = []
    if strict_c and not cg["pass"]:
        blocking.append("citation")
    if strict_f and not ff["pass"]:
        blocking.append("fact")
    if not jf["pass"]:
        blocking.append("jurisdiction")
    if not cu["pass"]:
        blocking.append("currency")
    return {"citation": cg, "fact": ff, "jurisdiction": jf, "currency": cu,
            "blocking": blocking, "pass": not blocking}


def block_message(report: dict) -> str:
    lines = ["Draft refused. The following must be fixed before this text can be written:"]
    for r in report["citation"]["unresolved"][:8]:
        lines.append(f"  CITATION {r['citation']} — {r['status']}. {r.get('note','')}")
    for s in report["citation"]["uncited_assertions"][:5]:
        lines.append(f"  UNCITED  \"{s}\" — states law with no authority.")
    for f in report["fact"]["unsourced_particulars"][:8]:
        lines.append(f"  FACT     {f['kind']} \"{f['text']}\" is not in the matter fact table. {f['fix']}")
    for f in report["jurisdiction"]["findings"][:5]:
        lines.append(f"  JURIS    {f.get('citation') or f.get('issue')} — {f.get('issue')}. {f.get('fix','')}")
    for f in report["currency"]["findings"][:5]:
        lines.append(f"  STALE    {f.get('citation')} — {f['issue']}. {f['fix']}")
    lines.append("Fix each item, or convert the unsupported material to a bracketed placeholder.")
    return "\n".join(lines)
