"""The gates. Nothing gets published that does not tie.

  NUMBER FENCE  every currency amount, percentage, and ratio in a report is
                backed by a [F#] figure whose stored value MATCHES. Catches
                both the invented number and the stale number copied forward
                after the data moved — which is the failure that actually
                happens in finance.
  TIE-OUT       report totals reconcile to the snapshot they claim to come
                from, within tolerance.
  FRESHNESS     the snapshot behind the report is not stale, and a final
                (non-preliminary) report requires a closed period.
  DEFINITION    every metric cited names its registry version, so a report
                cannot silently use a redefined metric.
"""
from __future__ import annotations
import re
from . import figures, snapshot, money, metrics
from ..runtime import setting

FIG_REF = re.compile(r"\[F(\d+)\]")
EST = re.compile(r"\[\[EST:[^\]]+\]\]")
TBD = re.compile(r"\[\[TBD:[^\]]+\]\]")

# What counts as a publishable number.
MONEY_TOK = re.compile(r"\(?-?\$\s?\d[\d,]*(?:\.\d+)?\)?")
PCT_TOK = re.compile(r"-?\d[\d,]*(?:\.\d+)?\s?%")
BARE_NUM = re.compile(r"(?<![\w$.-])-?\d[\d,]{2,}(?:\.\d+)?(?![\w%])")

# Numbers that are never financial assertions.
SAFE = re.compile(r"^(19|20)\d{2}$")          # years
NEAR = 120                                    # chars a [F#] may sit from its number


def _strip_masked(text: str) -> str:
    return TBD.sub(" ", EST.sub(" ", text))


def _figure_values() -> dict:
    vals = {}
    for f in figures.load()["figures"]:
        keys = {money.normalize_number_token(f.get("formatted", ""))}
        if f.get("value_cents") is not None:
            keys.add(money.normalize_number_token(str(f["value_cents"] / 100)))
        if f.get("raw") is not None:
            keys.add(money.normalize_number_token(str(f["raw"])))
            keys.add(str(f["raw"]))
        vals[f["id"]] = {"f": f, "keys": {k for k in keys if k}}
    return vals


def number_fence(text: str) -> dict:
    body = _strip_masked(text)
    figs = _figure_values()
    findings, checked = [], 0

    tokens = []
    for rx, kind in ((MONEY_TOK, "money"), (PCT_TOK, "percent"), (BARE_NUM, "number")):
        for m in rx.finditer(body):
            tok = m.group(0)
            if kind == "number" and SAFE.match(tok.replace(",", "")):
                continue
            tokens.append({"tok": tok, "kind": kind, "start": m.start(), "end": m.end()})

    # de-overlap: a money token also matches BARE_NUM
    tokens.sort(key=lambda t: (t["start"], -(t["end"] - t["start"])))
    kept, last_end = [], -1
    for t in tokens:
        if t["start"] >= last_end:
            kept.append(t)
            last_end = t["end"]

    consumed = set()
    for t in kept:
        checked += 1
        window = body[max(0, t["start"] - NEAR): t["end"] + NEAR]
        refs = [r for r in FIG_REF.findall(window) if f"F{r}" not in consumed]
        if not refs:
            findings.append({"issue": "unsourced_number", "text": t["tok"], "kind": t["kind"],
                             "offset": t["start"],
                             "fix": "compute it with metric_compute or ledger_query and cite the "
                                    "returned [F#], or mark it [[EST: basis]]"})
            continue
        want = money.normalize_number_token(t["tok"].rstrip("%"))
        matched = None
        for r in refs:
            fid = f"F{r}"
            entry = figs.get(fid)
            if not entry:
                findings.append({"issue": "unknown_figure", "text": t["tok"], "ref": fid,
                                 "fix": f"{fid} does not exist in the figure store"})
                matched = "bad"
                break
            if want in entry["keys"] or want.lstrip("-") in {k.lstrip("-") for k in entry["keys"]}:
                matched = fid
                consumed.add(fid)
                break
        if matched is None:
            refd = [{"ref": f"F{r}", "stored": (figs.get(f'F{r}') or {}).get("f", {}).get("formatted")}
                    for r in refs[:3]]
            findings.append({"issue": "figure_mismatch", "text": t["tok"], "offset": t["start"],
                             "referenced": refd,
                             "fix": "the number in the text does not match the figure it cites — "
                                    "recompute, or the data moved under a copied number",
                             "severity": "high"})
    return {"numbers_checked": checked, "findings": findings,
            "estimates_marked": len(EST.findall(text)),
            "pass": not findings}


def tieout(report_totals: dict, snapshot_id: str, tolerance_cents: int | None = None) -> dict:
    """report_totals: {label: cents}. Compares the sum against the snapshot total."""
    tol = tolerance_cents if tolerance_cents is not None else int(setting("tieout_tolerance_cents", 100))
    snap = snapshot.get(snapshot_id)
    if not snap:
        return {"pass": False, "findings": [{"issue": "unknown_snapshot", "snapshot": snapshot_id}]}
    if snap.get("total_cents") is None:
        return {"pass": False, "findings": [{"issue": "snapshot_total_unavailable",
                "note": "mixed currencies in the snapshot — an FX policy and rate date are required"}]}
    rep = sum(int(v) for v in report_totals.values())
    delta = rep - int(snap["total_cents"])
    ok = abs(delta) <= tol
    return {"pass": ok, "snapshot": snapshot_id,
            "report_total_cents": rep, "source_total_cents": snap["total_cents"],
            "report_total": money.fmt(rep), "source_total": money.fmt(int(snap["total_cents"])),
            "delta_cents": delta, "delta": money.fmt(delta), "tolerance_cents": tol,
            "findings": [] if ok else [{"issue": "does_not_tie", "delta": money.fmt(delta),
                                        "fix": "find the difference. Do not plug it."}]}


def freshness(snapshot_ids: list, final: bool, period_closed: bool) -> dict:
    hours = int(setting("snapshot_staleness_hours", 24))
    findings = []
    for sid in snapshot_ids:
        s = snapshot.get(sid)
        if not s:
            findings.append({"issue": "unknown_snapshot", "snapshot": sid})
        elif snapshot.is_stale(s, hours):
            findings.append({"issue": "stale_snapshot", "snapshot": sid,
                             "pulled_at": s["pulled_at"],
                             "fix": "re-pull before publishing"})
    if final and setting("require_period_close_for_final", True) and not period_closed:
        findings.append({"issue": "period_not_closed",
                         "fix": "label the report preliminary, or close the period first"})
    return {"findings": findings, "pass": not findings}


def definitions(text: str) -> dict:
    """Any metric named in the report should carry its registry version."""
    reg = metrics.registry()
    findings = []
    low = text.lower()
    for name, spec in reg.items():
        pretty = name.replace("_", " ")
        if name in low or pretty in low:
            if f"v{spec['version']}" not in text and spec["version"] not in text:
                findings.append({"metric": name, "version": spec["version"],
                                 "issue": "metric named without its definition version",
                                 "fix": f"cite as {name} (v{spec['version']}) or link the registry"})
    return {"findings": findings, "pass": not findings}


def run_all(text: str, snapshot_ids: list | None = None, report_totals: dict | None = None,
            tie_to: str | None = None, final: bool = False, period_closed: bool = False) -> dict:
    nf = number_fence(text)
    fr = freshness(snapshot_ids or [], final, period_closed)
    de = definitions(text)
    ti = tieout(report_totals, tie_to) if (report_totals and tie_to) else {"pass": True, "skipped": True}
    strict = str(setting("number_fence", "strict")) == "strict"
    blocking = []
    if strict and not nf["pass"]:
        blocking.append("numbers")
    if not ti.get("pass"):
        blocking.append("tieout")
    if not fr["pass"]:
        blocking.append("freshness")
    if not de["pass"]:
        blocking.append("definitions")
    return {"numbers": nf, "tieout": ti, "freshness": fr, "definitions": de,
            "blocking": blocking, "pass": not blocking}


def block_message(rep: dict) -> str:
    L = ["Report refused. Fix these before it can be written:"]
    for f in rep["numbers"]["findings"][:10]:
        if f["issue"] == "unsourced_number":
            L.append(f"  NUMBER    {f['text']} has no [F#] behind it. {f['fix']}")
        elif f["issue"] == "figure_mismatch":
            ref = ", ".join(f"{r['ref']}={r['stored']}" for r in f.get("referenced", []))
            L.append(f"  MISMATCH  {f['text']} does not match {ref}. {f['fix']}")
        else:
            L.append(f"  FIGURE    {f.get('text')} -> {f.get('ref')} unknown. {f['fix']}")
    if not rep["tieout"].get("pass") and not rep["tieout"].get("skipped"):
        t = rep["tieout"]
        L.append(f"  TIE-OUT   report {t.get('report_total')} vs source {t.get('source_total')}, "
                 f"off by {t.get('delta')}. Find it; do not plug it.")
    for f in rep["freshness"]["findings"][:5]:
        L.append(f"  FRESH     {f['issue']} {f.get('snapshot','')}. {f.get('fix','')}")
    for f in rep["definitions"]["findings"][:5]:
        L.append(f"  DEFINE    {f['metric']}: {f['issue']}. {f['fix']}")
    L.append("Every published number is traceable or it is marked [[EST: basis]].")
    return "\n".join(L)
