"""Claim graph. Do not average disagreements."""

from __future__ import annotations

import json
from typing import Any

from ..runtime import plugin_data_root
from . import bus

STANCES = frozenset({"supports", "contradicts", "qualifies", "silent"})


def claims_path():
    return plugin_data_root() / "claims.json"


def _load_unlocked() -> dict[str, Any]:
    path = claims_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def load_claims() -> dict[str, Any]:
    with bus.lock():
        return _load_unlocked()


def save_claims(data: dict[str, Any]) -> None:
    with bus.lock():
        bus.atomic_write(claims_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _next_cid(data: dict[str, Any]) -> str:
    highest = 0
    for key in data:
        if key.startswith("C") and key[1:].isdigit():
            highest = max(highest, int(key[1:]))
    return f"C{highest + 1}"


def upsert_claim(
    text: str,
    *,
    src: str,
    stance: str,
    conf: float = 0.5,
    span: int | None = None,
) -> dict[str, Any]:
    claim_text = text.strip()
    if not claim_text:
        return {"error": "claim text is required"}
    if stance not in STANCES:
        stance = "supports"
    with bus.lock():
        data = _load_unlocked()
        found_id = None
        for cid, node in data.items():
            if isinstance(node, dict) and node.get("text") == claim_text:
                found_id = cid
                break
        if found_id is None:
            found_id = _next_cid(data)
            data[found_id] = {"text": claim_text, "support": [], "status": "unsupported"}
        node = data[found_id]
        support = node.setdefault("support", [])
        if isinstance(support, list):
            support.append({"src": src, "stance": stance, "conf": conf, "span": span})
        node["status"] = _status(support if isinstance(support, list) else [])
        bus.atomic_write(claims_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return {"ok": True, "id": found_id, "claim": node}


def _status(support: list[Any]) -> str:
    stances = {
        str(item.get("stance"))
        for item in support
        if isinstance(item, dict)
    }
    if "contradicts" in stances and "supports" in stances:
        return "contested"
    if "supports" in stances:
        return "supported"
    return "unsupported"


def conflicts() -> list[dict[str, Any]]:
    data = load_claims()
    out: list[dict[str, Any]] = []
    for cid, node in data.items():
        if not isinstance(node, dict):
            continue
        if node.get("status") == "contested":
            out.append({"id": cid, **node})
    return out
