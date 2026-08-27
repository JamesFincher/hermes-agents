"""Tool schemas — what the LLM sees.

Official shape: name, description, parameters object.
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
"""

from __future__ import annotations

SOURCE_LEDGER_ADD = {
    "name": "source_ledger_add",
    "description": (
        "Record a retrieved primary source in the profile-scoped source ledger. "
        "Call this after you actually open a URL, paper, or official page. "
        "Do not add sources you did not retrieve. Dedupes on URL."
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
        "List sources already recorded in this profile's research ledger. "
        "Use before writing findings or when triage needs the current set."
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
        "Format citations from ledger IDs. Use when delivering a brief. "
        "Never invent bibliography entries — only IDs that exist in the ledger."
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
        "Check a claim against the ledger. Returns supporting overlaps or "
        "states that no recorded source covers the claim. Use before asserting a fact."
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
