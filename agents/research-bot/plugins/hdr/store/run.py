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
ACTIVE_CHILD_STATUSES = frozenset({"running", "briefed"})


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
        "spend": {
            "tokens": 0,
            "fetches": 0,
            "seconds": 0,
            "started_at": _now_iso(),
            "api_requests": {},
        },
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


def named_gaps(current: dict[str, Any] | None) -> list[str]:
    if not current:
        return []
    gaps = list(current.get("named_gaps") or [])
    if not gaps:
        gaps = list(current.get("open_questions") or [])
    return [str(item) for item in gaps if str(item).strip()]


def matches_named_gap(text: str, gaps: list[str]) -> bool:
    blob = (text or "").lower()
    if not blob or not gaps:
        return False
    for gap in gaps:
        needle = gap.strip().lower()
        if not needle:
            continue
        if needle in blob or blob in needle:
            return True
        if needle[:40] in blob or blob[:40] in needle:
            return True
    return False


def active_worker_count(current: dict[str, Any] | None) -> int:
    if not current:
        return 0
    children = current.get("children") or {}
    if not isinstance(children, dict):
        return 0
    count = 0
    for node in children.values():
        if isinstance(node, dict) and node.get("status") in ACTIVE_CHILD_STATUSES:
            count += 1
    return count


def worker_cap(current: dict[str, Any] | None) -> int:
    if not current:
        return 0
    budget = current.get("budget") or {}
    try:
        return int(budget.get("workers") or 0)
    except (TypeError, ValueError):
        return 0


def tick_wall_clock(data: dict[str, Any]) -> float:
    """Set spend.seconds from started_at. Wall time, not a sum of tool durations."""
    spend = data.setdefault("spend", {"tokens": 0, "fetches": 0, "seconds": 0})
    started = spend.get("started_at")
    if not started:
        spend["started_at"] = _now_iso()
        spend["seconds"] = 0.0
        return 0.0
    try:
        raw = str(started).replace("Z", "+00:00")
        started_at = datetime.fromisoformat(raw)
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        elapsed = max(0.0, (datetime.now(timezone.utc) - started_at).total_seconds())
    except (TypeError, ValueError):
        elapsed = float(spend.get("seconds") or 0)
    spend["seconds"] = elapsed
    return elapsed


def spend_ratio(data: dict[str, Any]) -> float:
    budget = data.get("budget") or {}
    spend = data.get("spend") or {}
    tokens = float(budget.get("tokens") or 1)
    fetches = float(budget.get("fetches") or 1)
    seconds = float(budget.get("seconds") or 1)
    token_ratio = float(spend.get("tokens") or 0) / tokens
    fetch_ratio = float(spend.get("fetches") or 0) / fetches
    second_ratio = float(spend.get("seconds") or 0) / seconds
    return max(token_ratio, fetch_ratio, second_ratio)


def governor_state(data: dict[str, Any]) -> str:
    tick_wall_clock(data)
    ratio = spend_ratio(data)
    if ratio >= 1.0:
        return "HARD"
    if ratio >= 0.85:
        return "RED"
    if ratio >= 0.60:
        return "AMBER"
    return "GREEN"


def emit_hard_brief(data: dict[str, Any]) -> str:
    """Write a ledger-only brief when the governor first hits HARD."""
    existing = str(data.get("hard_brief_path") or "")
    if existing and Path(existing).is_file():
        return existing
    from . import draft

    drafted = draft.draft_brief()
    text = str(drafted.get("brief") or "").strip() + "\n"
    run_id = str(data.get("run_id") or "unknown")
    dest = plugin_data_root() / "briefs" / f"{run_id}-partial.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    data["hard_brief_path"] = str(dest)
    bus.append_audit(
        run_id,
        {"event": "hard_brief", "path": str(dest), "bytes": len(text.encode("utf-8"))},
    )
    return str(dest)


def refresh_governor(data: dict[str, Any]) -> dict[str, Any]:
    prior = str(data.get("governor") or "GREEN")
    nxt = governor_state(data)
    data["governor"] = nxt
    if nxt != prior:
        bus.append_audit(
            str(data.get("run_id") or ""),
            {"event": "governor_transition", "from": prior, "to": nxt, "ratio": spend_ratio(data)},
        )
    saved = save_run(data)
    if nxt == "HARD" and prior != "HARD":
        emit_hard_brief(saved)
        saved = save_run(saved)
    return saved


def _request_record(spend: dict[str, Any], api_request_id: str) -> dict[str, Any]:
    requests = spend.setdefault("api_requests", {})
    if not isinstance(requests, dict):
        requests = {}
        spend["api_requests"] = requests
    node = requests.get(api_request_id)
    if not isinstance(node, dict):
        node = {"input": 0, "output": 0, "total": 0}
        requests[api_request_id] = node
    return node


def add_spend(
    *,
    tokens: int = 0,
    fetches: int = 0,
    seconds: float = 0,
    api_request_id: str = "",
    token_side: str = "",
    fetch_reason: str = "",
) -> dict[str, Any] | None:
    def _apply(data: dict[str, Any]) -> None:
        spend = data.setdefault("spend", {"tokens": 0, "fetches": 0, "seconds": 0})
        add_tokens = int(tokens)
        if api_request_id and add_tokens:
            record = _request_record(spend, api_request_id)
            side = token_side if token_side in {"input", "output", "total"} else "input"
            if side == "total" and int(record.get("input") or 0):
                add_tokens = 0
            elif int(record.get(side) or 0):
                add_tokens = 0
            else:
                record[side] = add_tokens
        spend["tokens"] = int(spend.get("tokens") or 0) + add_tokens
        if fetches:
            spend["fetches"] = int(spend.get("fetches") or 0) + int(fetches)
        if seconds:
            spend["seconds"] = float(spend.get("seconds") or 0) + float(seconds)
        if add_tokens:
            bus.append_audit(
                str(data.get("run_id") or ""),
                {
                    "event": "token_delta",
                    "api_request_id": api_request_id or None,
                    "tokens": add_tokens,
                    "side": token_side or None,
                },
            )
        if fetches:
            bus.append_audit(
                str(data.get("run_id") or ""),
                {
                    "event": "fetch_increment",
                    "reason": fetch_reason or "corpus_admission",
                    "fetches": int(fetches),
                },
            )
        prior = str(data.get("governor") or "GREEN")
        nxt = governor_state(data)
        data["governor"] = nxt
        if nxt != prior:
            bus.append_audit(
                str(data.get("run_id") or ""),
                {"event": "governor_transition", "from": prior, "to": nxt, "ratio": spend_ratio(data)},
            )
        if nxt == "HARD" and prior != "HARD":
            emit_hard_brief(data)

    return mutate_run(_apply)


def note_retrieval(
    *,
    created_corpus: bool,
    new_row: bool,
    nbytes: int,
    filled_bytes: bool = False,
    reason: str = "corpus_admission",
) -> dict[str, Any] | None:
    """Count a fetch only when a page body is newly stored."""
    admitted = bool(created_corpus or (nbytes > 0 and new_row) or filled_bytes)
    if not admitted:
        return load_run()
    return add_spend(fetches=1, fetch_reason=reason)


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
