from __future__ import annotations
from ..store import entity as E, gates, snapshot as S, mutations as MU
from ..runtime import setting


def transform_llm_output(response_text=None, session_id=None, **kwargs):
    try:
        if not response_text or len(response_text) < 200:
            return None
        extra = ""
        rep = gates.number_fence(response_text)
        unsourced = [f for f in rep["findings"] if f["issue"] == "unsourced_number"]
        mismatch = [f for f in rep["findings"] if f["issue"] == "figure_mismatch"]
        if mismatch:
            extra += ("\n\n> **Figure mismatch:** " +
                      "; ".join(f"{m['text']}" for m in mismatch[:5]) +
                      " does not match the figure cited. The underlying data may have moved "
                      "since this number was computed. Recompute before anyone uses it.")
        if unsourced:
            extra += ("\n\n> **Unsourced numbers:** " +
                      ", ".join(u["text"] for u in unsourced[:8]) +
                      ". These carry no [F#] and are not traceable to a snapshot.")
        e = E.load()
        if e:
            per = [p for p, v in (e.get("periods") or {}).items() if v.get("status") != "closed"]
            if per and any(p in response_text for p in per):
                extra += f"\n> **Preliminary:** period(s) {', '.join(sorted(per)[:3])} are not closed."
            pend = [p for p in MU.load()["proposals"]
                    if p["entity"] == e["entity_id"] and p["status"] == "proposed"]
            if pend:
                extra += (f"\n> **Awaiting your approval:** " +
                          ", ".join(f"{p['id']} {p['action']} {p.get('amount') or ''}" for p in pend[:3]) +
                          ". Nothing has been written to any system.")
        return (response_text + extra) if extra else None
    except Exception:
        return None
