"""Claim graph. Do not average disagreements."""

from __future__ import annotations

import json
from typing import Any

from ..runtime import plugin_data_root
from . import bus, ledger

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
            support[:] = [
                edge
                for edge in support
                if not (isinstance(edge, dict) and edge.get("src") == src)
            ]
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


def _cite_counts(data: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in data.values():
        if not isinstance(node, dict):
            continue
        for edge in node.get("support") or []:
            if not isinstance(edge, dict):
                continue
            sid = str(edge.get("src") or "")
            if sid:
                counts[sid] = counts.get(sid, 0) + 1
    return counts


def _edge_stamp(edge: dict[str, Any]) -> str:
    return str(edge.get("published") or edge.get("retrieved") or "")


def _is_section_conflict(support: list[dict[str, Any]], cite_counts: dict[str, int]) -> str | None:
    tier_a = [edge for edge in support if edge.get("tier") == "A"]
    a_stances = {str(edge.get("stance")) for edge in tier_a} - {"silent"}
    if "supports" in a_stances and "contradicts" in a_stances:
        return "tier-a"
    if not support:
        return None
    newest = max(support, key=_edge_stamp)
    most_cited = max(
        support,
        key=lambda edge: (cite_counts.get(str(edge.get("src") or ""), 0), _edge_stamp(edge)),
    )
    newest_stance = str(newest.get("stance") or "")
    cited_stance = str(most_cited.get("stance") or "")
    if (
        newest.get("src") != most_cited.get("src")
        and newest_stance in {"supports", "contradicts"}
        and cited_stance in {"supports", "contradicts"}
        and newest_stance != cited_stance
    ):
        return "newest-vs-most-cited"
    return None


def conflicts() -> list[dict[str, Any]]:
    data = load_claims()
    sources = {str(src.get("id")): src for src in ledger.list_sources() if src.get("id")}
    cite_counts = _cite_counts(data)
    out: list[dict[str, Any]] = []
    for cid, node in data.items():
        if not isinstance(node, dict):
            continue
        rows: list[dict[str, Any]] = []
        for edge in node.get("support") or []:
            if not isinstance(edge, dict):
                continue
            src = sources.get(str(edge.get("src") or "")) or {}
            rows.append(
                {
                    "src": edge.get("src"),
                    "stance": edge.get("stance"),
                    "tier": src.get("tier") or "D",
                    "retrieved": src.get("retrieved"),
                    "published": src.get("published"),
                }
            )
        reason = _is_section_conflict(rows, cite_counts)
        if not reason:
            continue
        out.append(
            {
                "id": cid,
                "text": node.get("text"),
                "status": node.get("status"),
                "reason": reason,
                "support": rows,
            }
        )
    return out
