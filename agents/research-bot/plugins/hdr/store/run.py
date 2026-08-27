"""Active run.json: plan, budget, tier, phase, saturation."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..runtime import TIER_BUDGET, TIERS, plugin_data_root, setting
from . import bus

PHASES = frozenset({"plan", "breadth", "gap", "depth", "synthesis", "verify", "done"})


def child_key(open_question: str) -> str:
    text = (open_question or "").strip()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
    return f"b-{digest}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_path() -> Path:
    return plugin_data_root() / "run.json"


def runs_dir() -> Path:
    path = plugin_data_root() / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def empty_run(question: str = "", tier: str | None = None) -> dict[str, Any]:
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
        "seen_ids": [],
        "updated_at": _now_iso(),
    }


def _load_unlocked() -> dict[str, Any] | None:
    path = run_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def _save_unlocked(data: dict[str, Any]) -> dict[str, Any]:
    data["updated_at"] = _now_iso()
    bus.atomic_write(run_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return data


def load_run() -> dict[str, Any] | None:
    with bus.lock():
        return _load_unlocked()


def save_run(data: dict[str, Any]) -> dict[str, Any]:
    with bus.lock():
        return _save_unlocked(data)


def mutate_run(mutator: Callable[[dict[str, Any]], None]) -> dict[str, Any] | None:
    """Load, change, and write run.json in one lock. Returns None if no run exists."""
    with bus.lock():
        data = _load_unlocked()
        if not data:
            return None
        mutator(data)
        return _save_unlocked(data)


def archive_run(data: dict[str, Any]) -> None:
    run_id = str(data.get("run_id") or "unknown")
    path = runs_dir() / f"{run_id}.json"
    with bus.lock():
        bus.atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def clear_run() -> None:
    """Remove the active run.json after archive. Next digest reports no active run."""
    path = run_path()
    with bus.lock():
        if path.is_file():
            path.unlink()


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
    def _apply(data: dict[str, Any]) -> None:
        spend = data.setdefault("spend", {"tokens": 0, "fetches": 0, "seconds": 0})
        spend["tokens"] = int(spend.get("tokens") or 0) + int(tokens)
        spend["fetches"] = int(spend.get("fetches") or 0) + int(fetches)
        spend["seconds"] = float(spend.get("seconds") or 0) + float(seconds)
        data["governor"] = governor_state(data)

    return mutate_run(_apply)


def bump_domain(host: str) -> dict[str, Any] | None:
    name = (host or "").strip().lower()
    if not name:
        return None

    def _apply(data: dict[str, Any]) -> None:
        counts = data.setdefault("domain_counts", {})
        if not isinstance(counts, dict):
            counts = {}
            data["domain_counts"] = counts
        counts[name] = int(counts.get(name) or 0) + 1

    return mutate_run(_apply)


def append_last_batch(ids: list[Any]) -> dict[str, Any] | None:
    def _apply(data: dict[str, Any]) -> None:
        batch = list(data.get("last_batch_ids") or [])
        for item in ids:
            if item and str(item) not in batch:
                batch.append(str(item))
        data["last_batch_ids"] = batch

    return mutate_run(_apply)


def record_query_hash(key: str, now: float, window_s: float) -> bool:
    """Record a search hash. Returns True when the same hash is still inside the window."""
    duplicate = False

    def _apply(data: dict[str, Any]) -> None:
        nonlocal duplicate
        seen = data.setdefault("query_hashes", {})
        if not isinstance(seen, dict):
            seen = {}
            data["query_hashes"] = seen
        prior = seen.get(key)
        if isinstance(prior, (int, float)) and now - float(prior) < window_s:
            duplicate = True
            return
        seen[key] = now

    if mutate_run(_apply) is None:
        return False
    return duplicate


def mark_mandate(open_question: str, status: str) -> dict[str, Any] | None:
    question = (open_question or "").strip()
    if not question:
        return None
    if status not in {"answered", "failed"}:
        status = "failed"

    def _apply(data: dict[str, Any]) -> None:
        mandates = data.setdefault("mandate_status", {})
        if not isinstance(mandates, dict):
            mandates = {}
            data["mandate_status"] = mandates
        mandates[question] = status
        if status == "answered":
            data["open_questions"] = [
                item for item in list(data.get("open_questions") or []) if str(item) != question
            ]

    return mutate_run(_apply)
