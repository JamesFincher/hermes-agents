"""research_plan and gap_scan."""

from __future__ import annotations

from typing import Any

from ..runtime import TIERS, dump, error
from ..store import claims as claim_store
from ..store import ledger, run


def research_plan(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        action = str((args or {}).get("action") or "create").lower()
        if action == "status":
            current = run.load_run()
            if not current:
                return error("no active run")
            return dump({"ok": True, **current})
        if action == "update":
            current = run.load_run() or run.empty_run()
        else:
            current = run.empty_run(
                question=str((args or {}).get("question") or ""),
                tier=str((args or {}).get("tier") or "standard"),
            )
        if (args or {}).get("question"):
            current["question"] = str(args["question"])
        if (args or {}).get("tier") in TIERS:
            from ..runtime import TIER_BUDGET

            current["tier"] = args["tier"]
            current["budget"] = dict(TIER_BUDGET[str(args["tier"])])
        if isinstance((args or {}).get("open_questions"), list):
            current["open_questions"] = [str(item) for item in args["open_questions"]]
        if isinstance((args or {}).get("falsifiers"), list):
            current["falsifiers"] = [str(item) for item in args["falsifiers"]]
        if isinstance((args or {}).get("constraints"), dict):
            current["constraints"] = args["constraints"]
        current["governor"] = run.governor_state(current)
        saved = run.save_run(current)
        return dump(
            {
                "ok": True,
                "run_id": saved["run_id"],
                "tier": saved["tier"],
                "budget": saved["budget"],
                "open_questions": saved.get("open_questions") or [],
                "phase": saved.get("phase") or "plan",
                "governor": saved.get("governor"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def gap_scan(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        detail = str((args or {}).get("detail") or "summary")
        current = run.load_run()
        sources = ledger.list_sources(run_id=(current or {}).get("run_id") or "")
        if not sources:
            sources = ledger.list_sources()
        open_qs = list((current or {}).get("open_questions") or [])
        unanswered: list[str] = []
        thin: list[dict[str, Any]] = []
        last_ids = list((current or {}).get("last_batch_ids") or [])
        new_count = 0
        prior = max(1, len(sources) - len(last_ids))
        for sid in last_ids:
            src = ledger.get_source(sid)
            if src and str(src.get("tier") or "") in {"A", "B"}:
                new_count += 1
        yield_ratio = new_count / max(1, len(last_ids)) if last_ids else 0.0
        for question in open_qs:
            support = [
                src
                for src in sources
                if question.lower()[:24] in str(src.get("title") or "").lower()
                or question.lower()[:24] in str(src.get("quote") or "").lower()
                or src.get("tier") in {"A", "B"}
            ]
            independent = {src.get("canonical_url") or src.get("url") for src in support}
            if len(independent) < 2:
                unanswered.append(question)
        for src in sources:
            if src.get("tier") in {"C", "D"} and src.get("id"):
                thin.append({"src": src["id"], "tier": src.get("tier"), "title": src.get("title")})
        graph = claim_store.conflicts()
        stale = [
            {"src": src.get("id"), "published": src.get("published")}
            for src in sources
            if src.get("needs_backfill")
        ]
        saturation = yield_ratio
        recommend = "synthesize"
        if unanswered and (current or {}).get("governor") in {None, "GREEN"}:
            recommend = "depth"
        if (current or {}).get("governor") in {"AMBER", "RED", "HARD"}:
            recommend = "stop" if (current or {}).get("governor") == "HARD" else "synthesize"
        if current:
            current["saturation"] = saturation
            current["new_source_yield"] = yield_ratio
            current["named_gaps"] = unanswered
            current["phase"] = "gap"
            run.save_run(current)
        payload: dict[str, Any] = {
            "ok": True,
            "saturation": saturation,
            "unanswered": unanswered,
            "thin": thin[:12],
            "conflicts": graph,
            "stale": stale,
            "recommend": recommend,
            "new_source_yield": yield_ratio,
            "sources": len(sources),
        }
        if detail != "full":
            payload["thin"] = payload["thin"][:5]
        return dump(payload)
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
