"""Schema'd factory store. Atomic writes. versioned migration."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from ..runtime import plugin_data

SCHEMA_VERSION = 2
STORE_NAME = "factory.json"
_LOCK = threading.Lock()
_COUNTER_LOCK = threading.Lock()
_COUNTER = 0


def _empty() -> dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "probes": [],
        "cards": [],
        "scaffolds": [],
        "checks": [],
        "audit": [],
        "governor": {"requests": 0, "input_tokens": 0, "state": "OK"},
        "plans": {},
    }


def migrate(payload: dict[str, Any] | None) -> dict[str, Any]:
    data = _empty()
    if not isinstance(payload, dict):
        return data
    incoming = dict(payload)
    version = incoming.get("version")
    if version is None:
        incoming["version"] = SCHEMA_VERSION
    data.update({key: incoming[key] for key in data if key in incoming})
    for key in ("probes", "cards", "scaffolds", "checks", "audit"):
        if not isinstance(data.get(key), list):
            data[key] = []
    if not isinstance(data.get("plans"), dict):
        data["plans"] = {}
    gov = data.get("governor")
    if not isinstance(gov, dict):
        data["governor"] = {"requests": 0, "input_tokens": 0, "state": "OK"}
    data["version"] = SCHEMA_VERSION
    return data


def store_path() -> Path:
    return plugin_data() / STORE_NAME


def _read_unlocked() -> dict[str, Any]:
    path = store_path()
    if not path.is_file():
        return migrate(None)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return migrate(None)
    if not isinstance(raw, dict):
        return migrate(None)
    return migrate(raw)


def _write_unlocked(payload: dict[str, Any]) -> dict[str, Any]:
    data = migrate(payload)
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    blob = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(blob, encoding="utf-8")
    tmp.replace(path)
    return data


def load_store() -> dict[str, Any]:
    with _LOCK:
        return _read_unlocked()


def save_store(payload: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        return _write_unlocked(payload)


def _next_id(prefix: str) -> str:
    global _COUNTER
    with _COUNTER_LOCK:
        _COUNTER += 1
        return f"{prefix}{_COUNTER}"


def _append(bucket: str, row: dict[str, Any], prefix: str) -> dict[str, Any]:
    with _LOCK:
        data = _read_unlocked()
        item = dict(row)
        item["id"] = item.get("id") or _next_id(prefix)
        data.setdefault(bucket, []).append(item)
        _write_unlocked(data)
        return item


def add_probe(row: dict[str, Any]) -> dict[str, Any]:
    return _append("probes", row, "P")


def add_card(row: dict[str, Any]) -> dict[str, Any]:
    return _append("cards", row, "C")


def add_scaffold(row: dict[str, Any]) -> dict[str, Any]:
    return _append("scaffolds", row, "S")


def add_check(row: dict[str, Any]) -> dict[str, Any]:
    return _append("checks", row, "K")


def add_audit(action: str, detail: str) -> dict[str, Any]:
    return _append("audit", {"action": action, "detail": detail}, "A")


def digest_payload(max_chars: int) -> str:
    data = load_store()
    gov = data.get("governor") if isinstance(data.get("governor"), dict) else {}
    lines = [
        f"probes={len(data.get('probes') or [])}",
        f"cards={len(data.get('cards') or [])}",
        f"scaffolds={len(data.get('scaffolds') or [])}",
        f"checks={len(data.get('checks') or [])}",
        f"plans={len(data.get('plans') or {})}",
        f"governor={gov.get('state', 'OK')} req={gov.get('requests', 0)}",
    ]
    last_probe = (data.get("probes") or [{}])[-1] if data.get("probes") else {}
    if last_probe:
        lines.append(
            f"last_probe={last_probe.get('knob')} {last_probe.get('tag')} "
            f"{last_probe.get('decision')}"
        )
    text = "factory " + " ".join(str(part) for part in lines)
    return text[: max(0, int(max_chars))]
