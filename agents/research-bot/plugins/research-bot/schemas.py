"""Tool schemas — what the LLM sees.

Official shape: name, description, parameters object.
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
"""

from __future__ import annotations

RESOLVE_LIBRARY = {
    "name": "resolve_library",
    "description": (
        "When to call: the user named a library, SDK, or product and you need "
        "its Context7 library ID before querying docs. Calls the profile "
        "Context7 MCP server via the plugin (ctx.call_mcp). Do not call raw "
        "mcp_context7_* / mcp_* tools. Records the hit in the source ledger."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Library name or search query (e.g. hermes-agent).",
            },
            "library_name": {
                "type": "string",
                "description": "Optional exact library name hint.",
            },
        },
        "required": ["query"],
    },
}

DOCS_QUERY = {
    "name": "docs_query",
    "description": (
        "When to call: you already have a Context7 library ID from "
        "resolve_library and need documentation text. Calls Context7 via the "
        "plugin. Do not call raw mcp_* tools. Records the hit in the ledger."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "library_id": {
                "type": "string",
                "description": "Context7 library ID from resolve_library.",
            },
            "query": {
                "type": "string",
                "description": "Documentation question.",
            },
            "tokens": {
                "type": "integer",
                "description": "Optional token budget.",
            },
        },
        "required": ["library_id", "query"],
    },
}

SOURCE_LEDGER_ADD = {
    "name": "source_ledger_add",
    "description": (
        "When to call: after you actually opened a non-Context7 page "
        "(web_search, web_extract, arXiv, official docs). Do not add sources "
        "you did not retrieve. Dedupes on URL."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Retrieved URL or stable identifier (https://… or doi:…)",
            },
            "title": {
                "type": "string",
                "description": "Document title as it appears on the page",
            },
            "quote": {
                "type": "string",
                "description": "Short supporting excerpt copied from the retrieved page",
            },
            "kind": {
                "type": "string",
                "description": "Source kind: docs, paper, source, web",
            },
        },
        "required": ["url"],
    },
}

SOURCE_LEDGER_LIST = {
    "name": "source_ledger_list",
    "description": (
        "When to call: before writing findings, or when triage needs the "
        "current recorded set."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional substring filter over url, title, quote, kind",
            },
        },
        "required": [],
    },
}

SOURCE_LEDGER_CITE = {
    "name": "source_ledger_cite",
    "description": (
        "When to call (cite_source): before citing a claim or delivering a "
        "brief. Use only this formatted text. Never invent bibliography "
        "entries — only IDs that exist in the ledger."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Ledger IDs to cite. Omit to cite the full ledger.",
            },
            "style": {
                "type": "string",
                "description": "apa, ieee, or chicago. Defaults to plugin settings.",
            },
        },
        "required": [],
    },
}

SOURCE_LEDGER_CHECK = {
    "name": "source_ledger_check",
    "description": (
        "When to call: before asserting a fact. Returns lexical overlaps or "
        "states that no recorded source covers the claim."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "claim": {
                "type": "string",
                "description": "The claim to check against recorded sources",
            },
        },
        "required": ["claim"],
    },
}
