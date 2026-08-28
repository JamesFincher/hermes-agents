"""Context7 facades + HTTP scholar/archive. No invented MCP servers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..runtime import (
    MCP_QUERY_TOOL,
    MCP_RESOLVE_TOOL,
    call_mcp,
    dump,
    error,
    first_openable_url,
    normalize_envelope,
)
from ..store import ledger, run


def _http_json(url: str, timeout: int = 20) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "hdr-research-bot/2.0 (https://github.com/JamesFincher/hermes-agents)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    if not raw:
        return None
    return json.loads(raw)


def resolve_library(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        query = str((args or {}).get("query") or (args or {}).get("library_name") or "").strip()
        if not query:
            return error("query is required")
        payload: dict[str, Any] = {"query": query}
        payload["libraryName"] = str((args or {}).get("library_name") or query)
        envelope = normalize_envelope(call_mcp(MCP_RESOLVE_TOOL, payload))
        blob = json.dumps(envelope, ensure_ascii=False)
        url = first_openable_url(blob)
        if url:
            current = run.load_run()
            ledger.add_source(
                {
                    "url": url,
                    "title": f"Context7 resolve: {query[:80]}",
                    "origin": "mcp:context7",
                    "kind": "primary",
                    "tier": "A",
                    "tier_reason": "first-party",
                    "run_id": (current or {}).get("run_id") or "",
                    "needs_backfill": True,
                    "quote": blob[:400],
                }
            )
        return dump({**envelope, "openable_url": url or None, "ledger": bool(url)})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def docs_query(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        library_id = str((args or {}).get("library_id") or "").strip()
        query = str((args or {}).get("query") or "").strip()
        if not library_id or not query:
            return error("library_id and query are required")
        payload: dict[str, Any] = {"libraryId": library_id, "query": query}
        if (args or {}).get("tokens") is not None:
            try:
                payload["tokens"] = int(args["tokens"])
            except (TypeError, ValueError):
                pass
        envelope = normalize_envelope(call_mcp(MCP_QUERY_TOOL, payload))
        blob = json.dumps(envelope, ensure_ascii=False)
        url = first_openable_url(blob)
        if url:
            current = run.load_run()
            ledger.add_source(
                {
                    "url": url,
                    "title": f"Context7 docs: {query[:80]}",
                    "origin": "mcp:context7",
                    "kind": "primary",
                    "tier": "A",
                    "tier_reason": "first-party",
                    "run_id": (current or {}).get("run_id") or "",
                    "needs_backfill": True,
                    "quote": blob[:400],
                }
            )
        return dump({**envelope, "openable_url": url or None, "ledger": bool(url)})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def scholar_search(args: dict[str, Any], **kwargs: Any) -> str:
    # Returns cards here. The Evidence Bus hook does not ingest this tool.
    # That keeps Crossref JSON out of the corpus.
    task_id = kwargs.get("task_id")
    del task_id
    try:
        query = str((args or {}).get("query") or "").strip()
        if not query:
            return error("query is required")
        limit = int((args or {}).get("limit") or 8)
        mailto = os.environ.get("CROSSREF_MAILTO") or os.environ.get("UNPAYWALL_EMAIL") or ""
        params = {"query": query, "rows": str(max(1, min(limit, 20)))}
        if mailto:
            params["mailto"] = mailto
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
        try:
            payload = _http_json(url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            return dump({"ok": False, "error": f"crossref unavailable: {exc}", "cards": []})
        items = (((payload or {}).get("message") or {}).get("items")) or []
        cards = []
        current = run.load_run()
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            doi = str(item.get("DOI") or "")
            title_list = item.get("title") or []
            title = str(title_list[0]) if title_list else doi
            openable = f"https://doi.org/{doi}" if doi else ""
            oa = None
            if doi and os.environ.get("UNPAYWALL_EMAIL"):
                try:
                    unpay = _http_json(
                        "https://api.unpaywall.org/v2/"
                        + urllib.parse.quote(doi)
                        + "?"
                        + urllib.parse.urlencode({"email": os.environ["UNPAYWALL_EMAIL"]})
                    )
                    best = (unpay or {}).get("best_oa_location") or {}
                    oa = best.get("url_for_pdf") or best.get("url")
                except Exception:
                    oa = None
            if openable:
                added = ledger.add_source(
                    {
                        "url": openable,
                        "title": title,
                        "doi": doi or None,
                        "published": str((item.get("issued") or {}).get("date-parts") or ""),
                        "origin": "scholar",
                        "kind": "primary",
                        "tier": "A",
                        "tier_reason": "peer-reviewed",
                        "run_id": (current or {}).get("run_id") or "",
                        "needs_backfill": True,
                    }
                )
                sid = (added.get("source") or {}).get("id")
            else:
                sid = None
            cards.append(
                {
                    "id": sid,
                    "title": title,
                    "doi": doi,
                    "url": openable,
                    "oa": oa,
                    "publisher": (item.get("publisher") or ""),
                }
            )
        return dump({"ok": True, "count": len(cards), "cards": cards})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def archive_lookup(args: dict[str, Any], **kwargs: Any) -> str:
    task_id = kwargs.get("task_id")
    del task_id
    try:
        url = str((args or {}).get("url") or "").strip()
        if not url:
            return error("url is required")
        cdx = (
            "https://web.archive.org/cdx/search/cdx?"
            + urllib.parse.urlencode(
                {
                    "url": url,
                    "output": "json",
                    "limit": "1",
                    "filter": "statuscode:200",
                    "fl": "timestamp,original,statuscode",
                }
            )
        )
        try:
            rows = _http_json(cdx)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            return dump({"ok": False, "error": f"wayback unavailable: {exc}"})
        if not isinstance(rows, list) or len(rows) < 2:
            return dump({"ok": False, "error": "no archived snapshot", "url": url})
        header, first = rows[0], rows[1]
        if not isinstance(first, list):
            return dump({"ok": False, "error": "malformed cdx", "url": url})
        fields = {str(name): first[i] for i, name in enumerate(header) if i < len(first)}
        stamp = fields.get("timestamp") or (first[0] if first else "")
        archived = f"https://web.archive.org/web/{stamp}/{url}" if stamp else ""
        current = run.load_run()
        if archived:
            ledger.add_source(
                {
                    "url": url,
                    "archived_url": archived,
                    "title": f"Wayback {stamp}",
                    "origin": "archive",
                    "fetch_status": "archived",
                    "run_id": (current or {}).get("run_id") or "",
                    "needs_backfill": True,
                }
            )
        return dump({"ok": True, "url": url, "archived_url": archived, "timestamp": stamp})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
