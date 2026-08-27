"""Tools this native plugin registers.

Official adding-tools danger box: return json.dumps string, never a dict;
errors are {"error": "..."}, never raise; handler(args: dict, **kwargs);
task_id = kwargs.get("task_id").
https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
"""

from __future__ import annotations

import json
from typing import Any

from . import ledger, runtime


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True)


def _normalize_envelope(envelope: Any) -> dict[str, Any]:
    if isinstance(envelope, dict):
        if "ok" in envelope or "error" in envelope:
            return envelope
        return {"ok": True, "result": envelope}
    if isinstance(envelope, str):
        try:
            loaded = json.loads(envelope)
        except json.JSONDecodeError:
            return {"ok": True, "result": envelope}
        if isinstance(loaded, dict):
            return loaded
        return {"ok": True, "result": loaded}
    return {"ok": True, "result": envelope}


def resolve_library(args: dict[str, Any], **kwargs: Any) -> str:
    kwargs.get("task_id")  # official per-call id; ledger is profile-scoped
    try:
        query = str(args.get("query") or "").strip()
        if not query:
            return _dumps({"error": "query is required"})
        payload: dict[str, Any] = {"query": query}
        if args.get("library_name"):
            payload["libraryName"] = str(args["library_name"])
        envelope = _normalize_envelope(
            runtime.call_mcp(runtime.MCP_RESOLVE_TOOL, payload)
        )
        snippet = str(envelope.get("result", envelope.get("error", envelope)))[:400]
        ledger.add_source(
            url=f"context7://resolve-library-id?q={query}",
            title=f"Context7 resolve_library: {query[:80]}",
            quote=snippet,
            kind="docs",
            origin="resolve_library",
        )
        return _dumps(envelope)
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def docs_query(args: dict[str, Any], **kwargs: Any) -> str:
    kwargs.get("task_id")  # official per-call id; ledger is profile-scoped
    try:
        library_id = str(args.get("library_id") or "").strip()
        query = str(args.get("query") or "").strip()
        if not library_id or not query:
            return _dumps({"error": "library_id and query are required"})
        payload: dict[str, Any] = {"libraryId": library_id, "query": query}
        if args.get("tokens") is not None:
            try:
                payload["tokens"] = int(args["tokens"])
            except (TypeError, ValueError):
                pass
        envelope = _normalize_envelope(
            runtime.call_mcp(runtime.MCP_QUERY_TOOL, payload)
        )
        snippet = str(envelope.get("result", envelope.get("error", envelope)))[:400]
        ledger.add_source(
            url=f"context7://query-docs?library={library_id}",
            title=f"Context7 docs_query: {query[:80]}",
            quote=snippet,
            kind="docs",
            origin="docs_query",
        )
        return _dumps(envelope)
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def source_ledger_add(args: dict[str, Any], **kwargs: Any) -> str:
    kwargs.get("task_id")  # official per-call id; ledger is profile-scoped
    try:
        url = str(args.get("url") or "").strip()
        if not url:
            return _dumps({"error": "url is required"})
        return _dumps(
            ledger.add_source(
                url=url,
                title=str(args.get("title") or url).strip(),
                quote=str(args.get("quote") or "").strip(),
                kind=str(args.get("kind") or "web").strip() or "web",
                origin=str(args.get("origin") or "tool").strip(),
            )
        )
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def source_ledger_list(args: dict[str, Any], **kwargs: Any) -> str:
    kwargs.get("task_id")  # official per-call id; ledger is profile-scoped
    try:
        return _dumps(ledger.list_sources(query=str(args.get("query") or "")))
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def cite_source(args: dict[str, Any], **kwargs: Any) -> str:
    kwargs.get("task_id")  # official per-call id; ledger is profile-scoped
    try:
        ids_raw = args.get("ids")
        ids: list[int] | None = None
        if isinstance(ids_raw, list):
            parsed: list[int] = []
            for item in ids_raw:
                try:
                    parsed.append(int(item))
                except (TypeError, ValueError):
                    return _dumps({"error": f"invalid ledger id: {item!r}"})
            ids = parsed
        style = str(args.get("style") or runtime.citation_style()).strip().lower()
        if style not in runtime.CITATION_STYLES:
            style = runtime.citation_style()
        return _dumps(ledger.cite_sources(ids, style))
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})


def source_ledger_check(args: dict[str, Any], **kwargs: Any) -> str:
    kwargs.get("task_id")  # official per-call id; ledger is profile-scoped
    try:
        claim = str(args.get("claim") or "").strip()
        if not claim:
            return _dumps({"error": "claim is required"})
        return _dumps(ledger.check_claim(claim))
    except Exception as exc:  # noqa: BLE001
        return _dumps({"error": str(exc)})
