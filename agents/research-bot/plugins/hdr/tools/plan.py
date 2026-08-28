"""research_plan and gap_scan."""

from __future__ import annotations

from typing import Any

from ..runtime import SATURATION_YIELD_LIMIT, TIER_BUDGET, TIERS, dump, error
from ..store import claims as claim_store
from ..store import ledger, run
from ..store import support as support_mod

_ACTIONS = frozenset({"create", "update", "status"})
_DETAILS = frozenset({"summary", "full"})


def _plan_envelope(current: dict[str, Any]) -> dict[str, Any]:
    budget = current.get("budget") or {}
    return {
        "ok": True,
        "run_id": current.get("run_id"),
        "tier": current.get("tier"),
        "budget": {
            "tokens": budget.get("tokens"),
            "fetches": budget.get("fetches"),
            "seconds": budget.get("seconds"),
        },
        "open_questions": current.get("open_questions") or [],
        "phase": current.get("phase") or "plan",
    }


def research_plan(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        # The deep-research-run skill writes todos. This tool does not invent a todo API.
        payload = args or {}
        action = str(payload.get("action") or "create").lower()
        if action not in _ACTIONS:
            return error("action must be create, update, or status")
        current = run.load_run()
        if current:
            current = run.refresh_governor(current)
        governor = (current or {}).get("governor") or "GREEN"
        if governor in {"RED", "HARD"} and action != "status":
            if not current:
                return error("no active run")
            envelope = _plan_envelope(current)
            envelope["governor"] = current.get("governor")
            envelope["note"] = f"governor {governor}: status only"
            return dump(envelope)
        if action == "status":
            if not current:
                return error("no active run")
            return dump(_plan_envelope(current))
        if payload.get("tier") not in (None, "") and payload.get("tier") not in TIERS:
            return error("tier must be quick, standard, deep, or exhaustive")
        if action == "update":
            current = current or run.empty_run()
        elif payload.get("tier"):
            current = run.empty_run(
                question=str(payload.get("question") or ""),
                tier=str(payload.get("tier")),
            )
        else:
            current = run.empty_run(question=str(payload.get("question") or ""))
        if payload.get("question"):
            current["question"] = str(payload["question"])
        if payload.get("tier") in TIERS and governor not in {"RED", "HARD"}:
            current["tier"] = payload["tier"]
            current["budget"] = dict(TIER_BUDGET[str(payload["tier"])])
        if isinstance(payload.get("open_questions"), list):
            current["open_questions"] = [str(item) for item in payload["open_questions"]]
        if isinstance(payload.get("falsifiers"), list):
            current["falsifiers"] = [str(item) for item in payload["falsifiers"]]
        if isinstance(payload.get("constraints"), dict):
            current["constraints"] = payload["constraints"]
        saved = run.refresh_governor(current)
        envelope = _plan_envelope(saved)
        envelope["governor"] = saved.get("governor")
        return dump(envelope)
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def _recommend(
    governor: str | None,
    unanswered: list[str],
    yield_ratio: float,
    saturated: bool,
) -> str:
    if governor == "HARD":
        return "stop"
    if governor in {"AMBER", "RED"}:
        return "synthesize"
    if unanswered and governor in {None, "GREEN"}:
        return "depth"
    if saturated:
        return "synthesize"
    if yield_ratio < SATURATION_YIELD_LIMIT and not unanswered:
        return "synthesize"
    if not unanswered:
        return "synthesize"
    return "depth"


def gap_scan(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        detail = str((args or {}).get("detail") or "summary").lower()
        if detail not in _DETAILS:
            return error("detail must be summary or full")
        current = run.load_run()
        if current:
            current = run.refresh_governor(current)
        sources = ledger.list_sources(run_id=(current or {}).get("run_id") or "")
        if not sources:
            sources = ledger.list_sources()
        open_qs = list((current or {}).get("open_questions") or [])
        graph = claim_store.load_claims()
        unanswered: list[str] = []
        thin: list[dict[str, Any]] = []
        last_ids = [str(item) for item in ((current or {}).get("last_batch_ids") or [])]
        last_sources = []
        new_ab = 0
        for sid in last_ids:
            src = ledger.get_source(sid)
            if src:
                last_sources.append(src)
            if src and str(src.get("tier") or "") in {"A", "B"}:
                new_ab += 1
        yield_ratio = new_ab / len(last_sources) if last_sources else 0.0
        for question in open_qs:
            coverage = support_mod.question_coverage(question, sources, graph)
            if coverage["support"] < 2:
                unanswered.append(question)
            support_rows = coverage["sources"]
            if support_rows and all(str(src.get("tier") or "D") in {"C", "D"} for src in support_rows):
                thin.append({"q": question, "support": coverage["support"], "tiers": coverage["tiers"]})
        for cid, node in graph.items():
            if not isinstance(node, dict):
                continue
            supporters = [
                ledger.get_source(str(edge.get("src") or ""))
                for edge in (node.get("support") or [])
                if isinstance(edge, dict) and edge.get("stance") == "supports"
            ]
            present = [src for src in supporters if src]
            if present and all(str(src.get("tier") or "D") in {"C", "D"} for src in present):
                thin.append(
                    {
                        "claim": cid,
                        "text": node.get("text"),
                        "support": len(present),
                    }
                )
        since = ((current or {}).get("constraints") or {}).get("since") if current else None
        stale = [
            {"src": src.get("id"), "published": src.get("published")}
            for src in sources
            if support_mod.is_stale(src.get("published"), since)
        ]
        backfill = [
            {"src": src.get("id"), "title": src.get("title")}
            for src in sources
            if src.get("needs_backfill")
        ]
        conflicts = claim_store.conflicts()
        governor = (current or {}).get("governor")
        yield_low = yield_ratio < SATURATION_YIELD_LIMIT
        covered = not unanswered
        saturated = bool(
            governor in {"AMBER", "RED", "HARD"} or (yield_low and covered and last_sources)
        )
        recommend = _recommend(
            str(governor) if governor is not None else None,
            unanswered,
            yield_ratio,
            saturated,
        )
        if current:
            current["saturation"] = yield_ratio
            current["new_source_yield"] = yield_ratio
            current["saturated"] = saturated
            current["named_gaps"] = unanswered
            current["phase"] = "gap"
            run.save_run(current)
        cap = 12 if detail == "full" else 5
        return dump(
            {
                "ok": True,
                "saturation": yield_ratio,
                "unanswered": unanswered,
                "thin": thin[:cap],
                "conflicts": conflicts,
                "stale": stale,
                "backfill": backfill,
                "recommend": recommend,
                "new_source_yield": yield_ratio,
                "saturated": saturated,
                "sources": len(sources),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
