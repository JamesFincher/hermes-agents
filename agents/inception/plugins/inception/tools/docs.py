"""Context7 facades. Openable URL or no stored card."""

from __future__ import annotations

from typing import Any

from ..runtime import MCP_QUERY_TOOL, MCP_RESOLVE_TOOL, call_mcp, dump, error, first_openable_url
from ..store import ledger


def docs_resolve(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload_in = args or {}
        query = str(payload_in.get("query") or "").strip()
        library_name = str(payload_in.get("library_name") or "").strip()
        if not query or not library_name:
            return error("query and library_name are required")
        envelope = call_mcp(
            MCP_RESOLVE_TOOL,
            {"query": query, "libraryName": library_name},
        )
        blob = dump(envelope) if isinstance(envelope, dict) else str(envelope)
        url = first_openable_url(blob)
        stored = None
        if url:
            stored = ledger.add_card(
                {
                    "source": "context7:resolve",
                    "query": query,
                    "library_name": library_name,
                    "openable_url": url,
                    "summary": blob[:400],
                    "untrusted": True,
                }
            )
            ledger.add_audit("docs_resolve", url)
        return dump(
            {
                "ok": bool(isinstance(envelope, dict) and envelope.get("ok", True)),
                "result": envelope.get("result") if isinstance(envelope, dict) else envelope,
                "error": envelope.get("error") if isinstance(envelope, dict) else None,
                "openable_url": url or None,
                "stored": bool(url),
                "card_id": None if not stored else stored.get("id"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def docs_ask(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload_in = args or {}
        library_id = str(payload_in.get("library_id") or "").strip()
        query = str(payload_in.get("query") or "").strip()
        if not library_id or not query:
            return error("library_id and query are required")
        envelope = call_mcp(
            MCP_QUERY_TOOL,
            {"libraryId": library_id, "query": query},
        )
        blob = dump(envelope) if isinstance(envelope, dict) else str(envelope)
        url = first_openable_url(blob)
        stored = None
        if url:
            stored = ledger.add_card(
                {
                    "source": "context7:query",
                    "query": query,
                    "library_id": library_id,
                    "openable_url": url,
                    "summary": blob[:400],
                    "untrusted": True,
                }
            )
            ledger.add_audit("docs_ask", url)
        return dump(
            {
                "ok": bool(isinstance(envelope, dict) and envelope.get("ok", True)),
                "result": envelope.get("result") if isinstance(envelope, dict) else envelope,
                "error": envelope.get("error") if isinstance(envelope, dict) else None,
                "openable_url": url or None,
                "stored": bool(url),
                "card_id": None if not stored else stored.get("id"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
