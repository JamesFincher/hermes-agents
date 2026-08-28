"""Cache-safe static sections + a hard-capped volatile digest.

The static sections are paid once per session and frozen on compaction. Only
turn-varying state goes through pre_llm_call, and it is capped here at 1000
characters by the plugin rather than by the platform's much larger limit.
"""
from __future__ import annotations
from ..store import matter as M, ledger as L

DIGEST_CAP = 1000


def section_gates(session_info=None) -> str:
    return (
        "LEX GATES — enforced in code, not by your good intentions.\n"
        "1. CITATION: every citation you write is extracted and resolved against the "
        "authority ledger. A citation you did not retrieve blocks the write. There is no "
        "phrasing that gets around this. Retrieve first, cite second.\n"
        "2. FACT: names, dates, money, addresses, dockets, and durations must come from "
        "the matter fact table or appear as [[FACT:key|what is needed]]. An invented "
        "particular blocks the write. A placeholder is a correct answer.\n"
        "3. JURISDICTION: authority from outside the matter's jurisdiction may not be "
        "described in binding language. Label it persuasive.\n"
        "4. CURRENCY: statutes, regulations, and rules go stale. Cases need a treatment "
        "check attempted. Stale or unchecked authority blocks the write.\n"
        "5. DEADLINES: deadline_compute refuses without a retrieved rule. Never state a "
        "date you did not compute from one.\n"
        "You are not counsel. You do not advise, file, appear, or predict outcomes. "
        "Everything you produce is for review by a licensed professional or by a person "
        "who understands they are representing themselves."
    )


def section_method(session_info=None) -> str:
    return (
        "LEX METHOD — order of operations.\n"
        "matter_open (jurisdiction, forum, posture, represented party) -> set_hat -> "
        "matter_fact for every fact you were actually given -> issue_plan -> "
        "worker_brief + delegate_task for authority, or authority_search inline for a "
        "narrow question -> read authority with authority_read before quoting it -> "
        "draft_scaffold for the required elements -> write the draft -> draft_check -> "
        "only then write the file.\n"
        "Load the hat skill (hat-litigation, hat-transactional, ...) for the document "
        "conventions of the current hat; the hat's body is not in this prompt on purpose.\n"
        "Authority preference: constitution > statute > regulation > binding case law > "
        "court rules > persuasive case law > secondary. Secondary sources are maps to "
        "primary law, never support for a proposition.\n"
        "When authority conflicts, show the conflict. When you did not find something, "
        "say what you searched. When you had to assume, name the assumption."
    )


def pre_llm_call(session_id=None, user_message=None, is_first_turn=False, **kwargs):
    try:
        m = M.load()
        if not m:
            return {"context": "[LEX] no active matter — matter_open before any drafting tool."}
        auths = L.search()
        unver = sum(1 for a in auths if not a.get("verified"))
        stale = sum(1 for a in auths if L.is_stale(a))
        open_iss = [i["question"] for i in m.get("issues", []) if i.get("status") == "open"]
        missing = [k for k in (m.get("open_questions") or [])][:3]
        line = (f"[LEX] {m['matter_id']} · {m.get('name','')[:40]} · {m['jurisdiction']}"
                f" · forum {m.get('forum')} · hat {m.get('hat') or 'UNSET'}\n"
                f"facts {len(m.get('facts', {}))} · authorities {len(auths)}"
                f" (unverified {unver}, stale {stale}) · open issues {len(open_iss)}\n")
        if open_iss:
            line += "open: " + "; ".join(q[:60] for q in open_iss[:3]) + "\n"
        if missing:
            line += "need from user: " + "; ".join(missing) + "\n"
        if not m.get("hat"):
            line += "set_hat before drafting.\n"
        return {"context": line[:DIGEST_CAP]}
    except Exception:
        return None  # fail open
