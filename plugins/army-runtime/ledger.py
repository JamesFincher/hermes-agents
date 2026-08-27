"""Durable source ledger in plugin-data/. Never the install tree."""

from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .runtime import plugin_data_root, session_state_get, session_state_set

_LEDGER_NAME = "source-ledger.json"
_SESSION_KEY = "ledger_ready"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ledger_path() -> Path:
    return plugin_data_root() / _LEDGER_NAME


def empty_ledger() -> dict[str, Any]:
    return {"version": 1, "updated_at": _now_iso(), "sources": []}


def init_ledger() -> dict[str, Any]:
    path = ledger_path()
    if not path.exists():
        data = empty_ledger()
        _write_ledger(data)
    else:
        data = load_ledger()
    session_state_set(_SESSION_KEY, True)
    return data


def load_ledger() -> dict[str, Any]:
    path = ledger_path()
    if not path.is_file():
        return empty_ledger()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return empty_ledger()
    if not isinstance(raw, dict):
        return empty_ledger()
    sources = raw.get("sources")
    if not isinstance(sources, list):
        raw["sources"] = []
    return raw


def _write_ledger(data: dict[str, Any]) -> None:
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


def _normalize_url(url: str) -> str:
    return url.strip()


def add_source(
    *,
    url: str,
    title: str = "",
    quote: str = "",
    kind: str = "web",
    retrieved: str = "",
    origin: str = "tool",
) -> dict[str, Any]:
    url = _normalize_url(url)
    if not url:
        return {"error": "url is required"}
    data = load_ledger()
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
            _write_ledger(data)
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
    _write_ledger(data)
    return {"ok": True, "updated": False, "source": entry}


def list_sources(query: str = "") -> dict[str, Any]:
    data = load_ledger()
    sources = [s for s in data.get("sources", []) if isinstance(s, dict)]
    needle = query.strip().lower()
    if needle:
        filtered: list[dict[str, Any]] = []
        for source in sources:
            blob = " ".join(
                str(source.get(key, "")) for key in ("url", "title", "quote", "kind")
            ).lower()
            if needle in blob:
                filtered.append(source)
        sources = filtered
    return {"ok": True, "count": len(sources), "sources": sources}


def get_sources_by_ids(ids: list[int]) -> list[dict[str, Any]]:
    wanted = set(ids)
    data = load_ledger()
    found: list[dict[str, Any]] = []
    for source in data.get("sources", []):
        if isinstance(source, dict) and source.get("id") in wanted:
            found.append(source)
    return found


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


def harvest_from_tool(tool_name: str, args: dict[str, Any], result: str) -> dict[str, Any]:
    """Pull URLs from web/file tool results into the ledger."""
    if tool_name in {
        "source_ledger_add",
        "source_ledger_list",
        "source_ledger_cite",
        "source_ledger_check",
    }:
        return {"ok": True, "harvested": 0, "skipped": "self"}
    added = 0
    urls = _extract_urls(tool_name, args, result)
    for item in urls:
        outcome = add_source(
            url=item["url"],
            title=item.get("title", ""),
            quote=item.get("quote", ""),
            kind=item.get("kind", "web"),
            origin=f"harvest:{tool_name}",
        )
        if outcome.get("ok"):
            added += 1
    return {"ok": True, "harvested": added}


def _extract_urls(
    tool_name: str, args: dict[str, Any], result: str
) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[str] = set()

    def _push(url: str, title: str = "", quote: str = "", kind: str = "web") -> None:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return
        if url in seen:
            return
        seen.add(url)
        found.append({"url": url, "title": title, "quote": quote, "kind": kind})

    arg_url = str(args.get("url") or args.get("uri") or "")
    if arg_url:
        _push(arg_url, title=str(args.get("title") or ""), kind="web")

    if tool_name in {"web_search", "web_extract", "read_file"}:
        kind = "file" if tool_name == "read_file" else "web"
        for match in re.findall(r"https?://[^\s\"'<>]+", result or ""):
            _push(match.rstrip(").,]}"), kind=kind)
        try:
            parsed = json.loads(result) if result else None
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            title = str(parsed.get("title") or parsed.get("name") or "")
            if arg_url and title:
                _push(arg_url, title=title)
            results = parsed.get("results") or parsed.get("items") or []
            if isinstance(results, list):
                for row in results:
                    if not isinstance(row, dict):
                        continue
                    _push(
                        str(row.get("url") or row.get("link") or ""),
                        title=str(row.get("title") or row.get("name") or ""),
                        quote=str(row.get("snippet") or row.get("content") or "")[:400],
                    )
    return found
