"""Claim graph. Do not average disagreements."""

from __future__ import annotations

import json
from datetime import datetime
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


def _source_tier(src: str, sources: dict[str, Any]) -> str:
    row = sources.get(src) or {}
    return str(row.get("tier") or "")


def _source_when(src: str, sources: dict[str, Any]) -> str:
    row = sources.get(src) or {}
    return str(row.get("published") or row.get("retrieved") or "")


def upsert_claim(
    text: str,
    *,
    src: str,
    stance: str,
    conf: float = 0.5,
    span: int | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    claim_text = text.strip()
    if not claim_text:
        return {"error": "claim text is required"}
    if stance not in STANCES:
        stance = "supports"
    sources = {str(item.get("id")): item for item in ledger.list_sources()}
    edge_tier = tier or _source_tier(src, sources)
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
            replaced = False
            for item in support:
                if isinstance(item, dict) and item.get("src") == src:
                    item["stance"] = stance
                    item["conf"] = conf
                    item["span"] = span
                    item["tier"] = edge_tier
                    replaced = True
                    break
            if not replaced:
                support.append(
                    {
                        "src": src,
                        "stance": stance,
                        "conf": conf,
                        "span": span,
                        "tier": edge_tier,
                    }
                )
        node["status"] = _status(support if isinstance(support, list) else [])
        bus.atomic_write(claims_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    ledger.link_claim(src, found_id)
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


def _parse_when(value: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        return datetime.min
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None)
    except ValueError:
        pass
    for size, fmt in ((10, "%Y-%m-%d"), (4, "%Y")):
        try:
            return datetime.strptime(raw[:size], fmt)
        except ValueError:
            continue
    return datetime.min


def _cite_counts(data: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in data.values():
        if not isinstance(node, dict):
            continue
        for item in node.get("support") or []:
            if not isinstance(item, dict):
                continue
            src = str(item.get("src") or "")
            if src:
                counts[src] = counts.get(src, 0) + 1
    return counts


def _tier_a_disagree(edges: list[dict[str, Any]]) -> bool:
    stances = {
        str(item.get("stance"))
        for item in edges
        if item.get("tier") == "A"
        and item.get("stance") in {"supports", "contradicts", "qualifies"}
    }
    if len(stances) <= 1:
        return False
    return bool(stances & {"supports", "contradicts", "qualifies"})


def _newest_vs_most_cited(
    edges: list[dict[str, Any]],
    sources: dict[str, Any],
    cite_counts: dict[str, int],
) -> bool:
    scored: list[dict[str, Any]] = []
    for item in edges:
        if not isinstance(item, dict) or not item.get("src"):
            continue
        if item.get("stance") not in {"supports", "contradicts", "qualifies"}:
            continue
        scored.append(item)
    if len(scored) < 2:
        return False
    newest = max(
        scored,
        key=lambda item: (
            _parse_when(_source_when(str(item.get("src")), sources)),
            str(item.get("src")),
        ),
    )
    most_cited = max(
        scored,
        key=lambda item: (
            cite_counts.get(str(item.get("src")), 0),
            str(item.get("src")),
        ),
    )
    if newest.get("src") == most_cited.get("src"):
        return False
    left = newest.get("stance")
    right = most_cited.get("stance")
    return left != right and {left, right} & {"supports", "contradicts"}


def conflicts() -> list[dict[str, Any]]:
    """Emit disagreements. Do not average them."""
    data = load_claims()
    sources = {str(item.get("id")): item for item in ledger.list_sources()}
    cite_counts = _cite_counts(data)
    out: list[dict[str, Any]] = []
    for cid, node in data.items():
        if not isinstance(node, dict):
            continue
        edges: list[dict[str, Any]] = []
        for item in node.get("support") or []:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["tier"] = row.get("tier") or _source_tier(str(row.get("src") or ""), sources)
            edges.append(row)
        if _tier_a_disagree(edges) or _newest_vs_most_cited(edges, sources, cite_counts):
            out.append({"id": cid, "text": node.get("text"), "status": node.get("status"), "support": edges})
    return out
