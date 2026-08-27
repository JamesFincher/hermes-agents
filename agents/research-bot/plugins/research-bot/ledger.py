"""Durable source ledger in plugin-data/. Thread-safe. Not session-keyed.

Agent-loop compression creates a child session lineage id. This file lives
at <HERMES_HOME>/plugin-data/research-bot/source-ledger.json so it survives
that rebuild. Do not key writes only to a discarded session id.
https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop

Concurrent ThreadPoolExecutor is the default for multiple tool_calls.
All ledger writes take _LOCK.
"""

from __future__ import annotations

import json
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .runtime import plugin_data_root, state_set

_LEDGER_NAME = "source-ledger.json"
_LOCK = threading.Lock()
_STOP = {
    "that",
    "this",
    "with",
    "from",
    "have",
    "been",
    "were",
    "they",
    "them",
    "their",
    "which",
    "into",
    "about",
    "after",
    "before",
    "where",
    "when",
    "your",
    "does",
    "using",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ledger_path() -> Path:
    return plugin_data_root() / _LEDGER_NAME


def empty_ledger() -> dict[str, Any]:
    return {"version": 1, "updated_at": _now_iso(), "sources": []}


def init_ledger() -> dict[str, Any]:
    with _LOCK:
        path = ledger_path()
        if not path.exists():
            data = empty_ledger()
            _write_ledger_unlocked(data)
        else:
            data = _load_ledger_unlocked()
        state_set("ledger_ready", True)
        return data


def load_ledger() -> dict[str, Any]:
    with _LOCK:
        return _load_ledger_unlocked()


def _load_ledger_unlocked() -> dict[str, Any]:
    path = ledger_path()
    if not path.is_file():
        return empty_ledger()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return empty_ledger()
    if not isinstance(raw, dict):
        return empty_ledger()
    if not isinstance(raw.get("sources"), list):
        raw["sources"] = []
    return raw


def _write_ledger_unlocked(data: dict[str, Any]) -> None:
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix="ledger-", suffix=".json", dir=str(path.parent))
    tmp_path = Path(tmp)
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        tmp_path.replace(path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def add_source(
    *,
    url: str,
    title: str = "",
    quote: str = "",
    kind: str = "web",
    retrieved: str = "",
    origin: str = "tool",
) -> dict[str, Any]:
    url = url.strip()
    if not url:
        return {"error": "url is required"}
    with _LOCK:
        data = _load_ledger_unlocked()
        sources = data["sources"]
        if not isinstance(sources, list):
            sources = []
            data["sources"] = sources
        for existing in sources:
            if isinstance(existing, dict) and existing.get("url") == url:
                if title and not existing.get("title"):
                    existing["title"] = title
                if quote and not existing.get("quote"):
                    existing["quote"] = quote
                if kind and existing.get("kind") == "web":
                    existing["kind"] = kind
                _write_ledger_unlocked(data)
                return {"ok": True, "updated": True, "source": existing}
        next_id = 1
        for existing in sources:
            if isinstance(existing, dict) and isinstance(existing.get("id"), int):
                next_id = max(next_id, int(existing["id"]) + 1)
        entry = {
            "id": next_id,
            "url": url,
            "title": title.strip(),
            "quote": quote.strip(),
            "kind": kind.strip() or "web",
            "retrieved": retrieved.strip() or _now_iso(),
            "origin": origin,
        }
        sources.append(entry)
        _write_ledger_unlocked(data)
        return {"ok": True, "updated": False, "source": entry}


def list_sources(query: str = "") -> dict[str, Any]:
    data = load_ledger()
    sources = [s for s in data.get("sources", []) if isinstance(s, dict)]
    needle = query.strip().lower()
    if needle:
        sources = [
            source
            for source in sources
            if needle
            in " ".join(
                str(source.get(key, "")) for key in ("url", "title", "quote", "kind")
            ).lower()
        ]
    return {"ok": True, "count": len(sources), "sources": sources}


def cite_sources(ids: list[int] | None, style: str) -> dict[str, Any]:
    data = load_ledger()
    sources = [s for s in data.get("sources", []) if isinstance(s, dict)]
    if ids:
        wanted = set(ids)
        sources = [s for s in sources if s.get("id") in wanted]
        missing = sorted(wanted - {s.get("id") for s in sources})
    else:
        missing = []
    citations = []
    for index, source in enumerate(sources, start=1):
        citations.append(
            {
                "id": source.get("id"),
                "n": index,
                "text": format_citation(source, style),
                "url": source.get("url"),
            }
        )
    return {
        "ok": True,
        "style": style,
        "count": len(citations),
        "citations": citations,
        "missing_ids": missing,
    }


def format_citation(source: dict[str, Any], style: str) -> str:
    title = str(source.get("title") or source.get("url") or "Untitled")
    url = str(source.get("url") or "")
    retrieved = str(source.get("retrieved") or "")
    year = ""
    match = re.search(r"(20\d{2}|19\d{2})", retrieved)
    if match:
        year = match.group(1)
    if style == "ieee":
        year_bit = f", {year}" if year else ""
        return f"{title}{year_bit}. {url}".strip()
    if style == "chicago":
        year_bit = f" ({year})" if year else ""
        return f'"{title}"{year_bit}. {url}'.strip()
    year_bit = f" ({year})." if year else "."
    return f"{title}{year_bit} {url}".strip()


def check_claim(claim: str) -> dict[str, Any]:
    text = claim.strip()
    if not text:
        return {"error": "claim is required"}
    data = load_ledger()
    sources = [s for s in data.get("sources", []) if isinstance(s, dict)]
    tokens = {t for t in re.findall(r"[a-z0-9]{4,}", text.lower()) if t not in _STOP}
    supporting: list[dict[str, Any]] = []
    for source in sources:
        blob = " ".join(
            str(source.get(key, "")) for key in ("url", "title", "quote")
        ).lower()
        overlap = [t for t in tokens if t in blob]
        if overlap:
            supporting.append(
                {
                    "id": source.get("id"),
                    "url": source.get("url"),
                    "title": source.get("title"),
                    "overlap": overlap[:12],
                }
            )
    return {
        "ok": True,
        "claim": text,
        "supported": bool(supporting),
        "ledger_size": len(sources),
        "supporting": supporting,
        "note": (
            "Supporting overlap is lexical, not proof. Open the URL."
            if supporting
            else "No ledger source overlaps this claim. Retrieve a primary page or do not state it as fact."
        ),
    }


def digest(limit: int = 5) -> str:
    listed = list_sources()
    sources = listed.get("sources") or []
    if not sources:
        return "LEDGER: empty. Resolve or cite a source before making a claim."
    lines = [f"LEDGER: {listed.get('count', 0)} source(s). Latest:"]
    for source in sources[-limit:]:
        title = str(source.get("title") or source.get("url") or "untitled")
        url = str(source.get("url") or "")
        lines.append(f"- [{source.get('id')}] {title} — {url}")
    return "\n".join(lines)
