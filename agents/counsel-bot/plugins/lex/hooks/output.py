"""transform_llm_output: deterministic footer + a last-line citation warning.

Costs zero inference tokens and cannot be forgotten by the model.
"""
from __future__ import annotations
from ..store import matter as M, gates, ledger as L
from ..runtime import setting

FOOTER = (
    "\n\n---\n"
    "*Drafted by an automated legal-drafting instrument. Not legal advice, not a lawyer, "
    "no attorney-client relationship. Every citation and every date must be independently "
    "verified by a licensed attorney in the relevant jurisdiction before use or filing.*"
)


def transform_llm_output(response_text=None, session_id=None, **kwargs):
    try:
        if not response_text or len(response_text) < 200:
            return None
        if not setting("disclaimer_footer", True):
            return None

        extra = ""
        rep = gates.citation_gate(response_text)
        bad = rep["unresolved"]
        if bad:
            listed = "; ".join(f"{b['citation']} ({b['status']})" for b in bad[:6])
            extra += ("\n\n> **Citation warning — unverified in this matter:** " + listed +
                      ". These were not retrieved into the authority ledger and must not be "
                      "relied on until they are.")
        if rep["uncited_assertions"]:
            extra += (f"\n> **{len(rep['uncited_assertions'])} statement(s) of law carry no "
                      "citation.** Treat them as unsupported.")

        m = M.load()
        if m:
            stale = [a["id"] for a in L.search() if L.is_stale(a)]
            if stale:
                extra += f"\n> **Stale authority in ledger:** {', '.join(stale[:8])}."

        if FOOTER.strip()[:40] in response_text:
            return response_text + extra if extra else None
        return response_text + extra + FOOTER
    except Exception:
        return None  # fail open
