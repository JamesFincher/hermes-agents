from __future__ import annotations
from ..store import entity as E, figures as F, snapshot as S, mutations as MU
from ..runtime import setting

DIGEST_CAP = 1000


def section_gates(session_info=None) -> str:
    return (
        "FIN GATES — enforced in code.\n"
        "1. NUMBER FENCE: every currency amount, percent, and ratio in a report must carry a "
        "[F#] figure reference whose stored value matches. An unsourced number blocks the "
        "write. A number that does not match the figure it cites blocks the write — that is "
        "the stale-copy error and it is the one that actually happens.\n"
        "2. TIE-OUT: report totals reconcile to their snapshot within tolerance. An "
        "unexplained difference is an open item. Never a plug.\n"
        "3. FRESHNESS: stale snapshots and unclosed periods block a FINAL report. Preliminary "
        "is a label, not a failure.\n"
        "4. DEFINITIONS: name a metric, cite its registry version.\n"
        "5. MUTATIONS: you cannot write to any system of record. You propose; a human approves "
        "a specific proposal id; only then does it apply, once, under an idempotency key.\n"
        "You never do arithmetic in prose. Every number comes from metric_compute, "
        "ledger_query, variance_report, cash_forecast, or execute_code. If you find yourself "
        "adding two figures in your head, stop and call a tool.\n"
        "You do not give investment, tax, or securities advice."
    )


def section_method(session_info=None) -> str:
    return (
        "FIN METHOD — pull, pin, compute, tie, write.\n"
        "entity_open (name, currency, basis) -> set_hat -> snapshot_pull per system -> "
        "ledger_query / metric_compute (each returns an [F#]) -> anomaly_scan -> "
        "recon_tieout -> report_scaffold -> write the draft citing [F#] -> report_check -> "
        "only then write the file.\n"
        "Load the hat skill (hat-controller, hat-fpa, hat-treasury, hat-ar-ap, "
        "hat-investor-reporting, hat-bookkeeping) for that role's conventions.\n"
        "Say cash or accrual, every time. Name the period. Name the snapshot.\n"
        "Lead with the number and the delta, then the driver, then the caveat. Bad news first. "
        "Material variances need a cause, not a category name. Anything forward-looking gets "
        "assumptions and a range, never a point estimate stated as fact."
    )


def pre_llm_call(session_id=None, user_message=None, is_first_turn=False, **kwargs):
    try:
        e = E.load()
        if not e:
            return {"context": "[FIN] no active entity — entity_open before any computation."}
        idx = S.index()["snapshots"]
        mine = [s for s in idx if s["entity"] == e["entity_id"]]
        pend = [p for p in MU.load()["proposals"]
                if p["entity"] == e["entity_id"] and p["status"] in ("proposed", "approved")]
        periods = e.get("periods", {})
        openp = [p for p, v in periods.items() if v.get("status") != "closed"]
        line = (f"[FIN] {e['entity_id']} · {e.get('name','')[:36]} · {e.get('home_currency')} · "
                f"{e.get('basis')} basis · hat {e.get('hat') or 'UNSET'}\n"
                f"snapshots {len(mine)}"
                + (f" (latest {mine[-1]['id']} {mine[-1]['source']} {mine[-1]['pulled_at'][:16]})" if mine else "")
                + f" · figures {len(F.by_period(e['entity_id'], ''))}+\n")
        if openp:
            line += "open periods: " + ", ".join(sorted(openp)[:4]) + "\n"
        if pend:
            line += (f"PENDING MUTATIONS awaiting human approval: "
                     + ", ".join(f"{p['id']}({p['action']} {p.get('amount') or ''})" for p in pend[:3])
                     + "\n")
        if e.get("open_items"):
            line += "open items: " + "; ".join(str(x)[:50] for x in e["open_items"][:2]) + "\n"
        return {"context": line[:DIGEST_CAP]}
    except Exception:
        return None
