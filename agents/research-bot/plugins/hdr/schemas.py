"""Flat model-facing schemas. Official: {name, description, parameters}.

https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
"""

from __future__ import annotations

RESEARCH_PLAN = {
    "name": "research_plan",
    "description": (
        "When to call: at the start of a research job, or to update/status the "
        "run. Writes run.json. Deterministic budget envelope. Not a prompt."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "update", "status"],
                "description": "create, update, or status",
            },
            "question": {"type": "string", "description": "Research question"},
            "tier": {
                "type": "string",
                "enum": ["quick", "standard", "deep", "exhaustive"],
                "description": "quick, standard, deep, or exhaustive",
            },
            "open_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Independently answerable questions",
            },
            "falsifiers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What would prove the working answer wrong",
            },
            "constraints": {
                "type": "object",
                "description": "since / domains / exclude",
            },
        },
        "required": [],
    },
}

GAP_SCAN = {
    "name": "gap_scan",
    "description": (
        "When to call: after a worker batch. Returns the saturation number. "
        "The model does not estimate saturation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "enum": ["summary", "full"],
                "description": "summary or full",
            }
        },
        "required": [],
    },
}

EVIDENCE_ADD = {
    "name": "evidence_add",
    "description": (
        "When to call: after you opened a PDF, file, or terminal-fetched page "
        "that the intake hook did not see. Canonicalizes and stores corpus."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Retrieved URL or doi:"},
            "title": {"type": "string"},
            "text": {"type": "string", "description": "Full retrieved text"},
            "quote": {"type": "string"},
            "kind": {"type": "string"},
            "origin": {"type": "string"},
        },
        "required": ["url"],
    },
}

EVIDENCE_SEARCH = {
    "name": "evidence_search",
    "description": (
        "When to call: any phase. Query the ledger/corpus. Returns cards, "
        "never full text."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search string"},
        },
        "required": ["query"],
    },
}

EVIDENCE_READ = {
    "name": "evidence_read",
    "description": (
        "When to call: only when a card span is not enough. Returns a byte "
        "range of a corpus file. The only sanctioned raw-text pull."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "src": {"type": "string", "description": "Ledger id such as S17"},
            "offset": {"type": "integer"},
            "limit": {"type": "integer"},
            "around_span": {"type": "integer"},
        },
        "required": ["src"],
    },
}

EVIDENCE_STATS = {
    "name": "evidence_stats",
    "description": "When to call: gap phase. Coverage numbers by tier and question.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

CLAIM_VERIFY = {
    "name": "claim_verify",
    "description": (
        "When to call: before asserting a fact. Exact-span provenance against "
        "the corpus. Not lexical overlap."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "claim": {"type": "string"},
            "candidate_sources": {
                "type": "array",
                "items": {"type": "string"},
            },
            "stance": {
                "type": "string",
                "description": "supports, contradicts, qualifies, or silent",
            },
        },
        "required": ["claim"],
    },
}

CONFLICT_REPORT = {
    "name": "conflict_report",
    "description": (
        "When to call: verify phase. Every claim where sources disagree. "
        "Do not average."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

CITATION_PASS = {
    "name": "citation_pass",
    "description": (
        "When to call: after a draft exists. Maps claims, then runs "
        "claim_verify. Uses official ctx.llm when the host exposes it. "
        "Falls back to a deterministic sweep. Not a moa toolset."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "draft": {"type": "string", "description": "Draft brief text"},
            "text": {"type": "string"},
        },
        "required": [],
    },
}

CITE_SOURCE = {
    "name": "cite_source",
    "description": (
        "When to call (cite_source): after every factual claim, and before "
        "delivering a brief. Use only this formatted text. Never invent "
        "bibliography entries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ledger ids such as S17. Omit to cite the run.",
            },
            "style": {
                "type": "string",
                "enum": ["apa", "ieee", "chicago"],
                "description": "apa, ieee, or chicago",
            },
        },
        "required": [],
    },
}

WORKER_BRIEF = {
    "name": "worker_brief",
    "description": (
        "When to call: before delegate_task. Compile a self-contained child "
        "brief. Returns text to paste into goal/context."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "open_question": {"type": "string"},
            "boundary": {"type": "string"},
            "must_find": {"type": "array", "items": {"type": "string"}},
            "source_types": {"type": "array", "items": {"type": "string"}},
            "max_fetches": {"type": "integer"},
            "return_format": {"type": "string"},
        },
        "required": ["open_question"],
    },
}

WORKER_HARVEST = {
    "name": "worker_harvest",
    "description": (
        "When to call: after a child finishes. Returns counts and ids only. "
        "Zero raw page text."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "subagent_id": {"type": "string"},
            "transcript_path": {"type": "string"},
            "brief_id": {"type": "string"},
            "open_question": {"type": "string"},
        },
        "required": [],
    },
}

RESOLVE_LIBRARY = {
    "name": "resolve_library",
    "description": (
        "When to call: resolve_library — the user named a library and you need "
        "its Context7 id. Facade over MCP. Must return an openable docs URL "
        "or the result does not enter the ledger. Do not call raw mcp_*."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "library_name": {"type": "string"},
        },
        "required": ["query"],
    },
}

DOCS_QUERY = {
    "name": "docs_query",
    "description": (
        "When to call: docs_query — you have a library id and need docs text. "
        "Must return an openable docs URL or it does not enter the ledger. "
        "Do not call raw mcp_*."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "library_id": {"type": "string"},
            "query": {"type": "string"},
            "tokens": {"type": "integer"},
        },
        "required": ["library_id", "query"],
    },
}

SCHOLAR_SEARCH = {
    "name": "scholar_search",
    "description": (
        "When to call: academic sweep. HTTP fallback (Crossref). "
        "Returns cards with DOI + OA link. No invented MCP server required."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"},
        },
        "required": ["query"],
    },
}

ARCHIVE_LOOKUP = {
    "name": "archive_lookup",
    "description": (
        "When to call: dead or changed URL. Wayback/Memento HTTP. Stores archived_url."
    ),
    "parameters": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
}

ALL = [
    RESEARCH_PLAN,
    GAP_SCAN,
    EVIDENCE_ADD,
    EVIDENCE_SEARCH,
    EVIDENCE_READ,
    EVIDENCE_STATS,
    CLAIM_VERIFY,
    CONFLICT_REPORT,
    CITATION_PASS,
    CITE_SOURCE,
    WORKER_BRIEF,
    WORKER_HARVEST,
    RESOLVE_LIBRARY,
    DOCS_QUERY,
    SCHOLAR_SEARCH,
    ARCHIVE_LOOKUP,
]
