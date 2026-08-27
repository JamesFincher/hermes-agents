"""Active run.json: plan, budget, tier, phase, saturation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..runtime import TIER_BUDGET, TIERS, plugin_data_root, setting
from . import bus

PHASES = frozenset({"plan", "breadth", "gap", "depth", "synthesis", "verify", "done"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_path() -> Path:
    return plugin_data_root() / "run.json"


def runs_dir() -> Path:
    path = plugin_data_root() / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def empty_run(question: str = "", tier: str = "standard") -> dict[str, Any]:
    chosen = tier if tier in TIERS else str(setting("default_tier", "standard"))
    if chosen not in TIERS:
        chosen = "standard"
    budget = dict(TIER_BUDGET[chosen])
    return {
        "run_id": f"r-{uuid.uuid4().hex[:6]}",
        "question": question,
        "tier": chosen,
        "phase": "plan",
        "open_questions": [],
        "falsifiers": [],
        "constraints": {},
        "budget": budget,
        "spend": {"tokens": 0, "fetches": 0, "seconds": 0, "started_at": _now_iso()},
        "saturation": None,
        "new_source_yield": None,
        "governor": "GREEN",
        "children": {},
        "last_batch_ids": [],
        "updated_at": _now_iso(),
    }


def load_run() -> dict[str, Any] | None:
    path = run_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def save_run(data: dict[str, Any]) -> dict[str, Any]:
    data["updated_at"] = _now_iso()
    with bus.lock():
        bus.atomic_write(run_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return data


def archive_run(data: dict[str, Any]) -> None:
    run_id = str(data.get("run_id") or "unknown")
    path = runs_dir() / f"{run_id}.json"
    with bus.lock():
        bus.atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def governor_state(data: dict[str, Any]) -> str:
    budget = data.get("budget") or {}
    spend = data.get("spend") or {}
    tokens = float(budget.get("tokens") or 1)
    fetches = float(budget.get("fetches") or 1)
    seconds = float(budget.get("seconds") or 1)
    token_ratio = float(spend.get("tokens") or 0) / tokens
    fetch_ratio = float(spend.get("fetches") or 0) / fetches
    second_ratio = float(spend.get("seconds") or 0) / seconds
    ratio = max(token_ratio, fetch_ratio, second_ratio)
    if ratio >= 1.0:
        return "HARD"
    if ratio >= 0.85:
        return "RED"
    if ratio >= 0.60:
        return "AMBER"
    return "GREEN"


def add_spend(
    *,
    tokens: int = 0,
    fetches: int = 0,
    seconds: float = 0,
) -> dict[str, Any] | None:
    data = load_run()
    if not data:
        return None
    spend = data.setdefault("spend", {"tokens": 0, "fetches": 0, "seconds": 0})
    spend["tokens"] = int(spend.get("tokens") or 0) + int(tokens)
    spend["fetches"] = int(spend.get("fetches") or 0) + int(fetches)
    spend["seconds"] = float(spend.get("seconds") or 0) + float(seconds)
    data["governor"] = governor_state(data)
    return save_run(data)
