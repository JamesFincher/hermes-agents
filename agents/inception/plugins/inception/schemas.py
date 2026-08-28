"""Flat model-facing schemas. Official: {name, description, parameters}.

https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
"""

from __future__ import annotations

DOCS_RESOLVE = {
    "name": "docs_resolve",
    "description": (
        "When to call: before any new Hermes or Honcho knob. Resolves a "
        "Context7 library id. The inception plugin registers this tool. "
        "Openable https URL or no stored card. Not a search tool. "
        "Does not copy resolve_library, docs_query, or cite_source from hdr."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What you need from the library docs",
            },
            "library_name": {
                "type": "string",
                "description": "Official library name, such as Hermes Agent",
            },
        },
        "required": ["query", "library_name"],
    },
}

DOCS_ASK = {
    "name": "docs_ask",
    "description": (
        "When to call: after docs_resolve, to read one official topic. "
        "Queries Context7. Returns a bounded card. Raw payload is stored "
        "only when an openable https URL is present."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "library_id": {
                "type": "string",
                "description": "Context7 id such as /nousresearch/hermes-agent",
            },
            "query": {
                "type": "string",
                "description": "One knob, hook, or contract question",
            },
        },
        "required": ["library_id", "query"],
    },
}

PROBE_KNOB = {
    "name": "probe_knob",
    "description": (
        "When to call: after you have an official page or a miss. Records "
        "accept / reject / default plus [DOC] / [INF] / [UNV]. [UNV] cannot "
        "set code_depends true."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "knob": {"type": "string", "description": "Exact key or hook name"},
            "decision": {
                "type": "string",
                "enum": ["accept", "reject", "default"],
                "description": "accept, reject, or default",
            },
            "tag": {
                "type": "string",
                "enum": ["DOC", "INF", "UNV"],
                "description": "DOC needs a url. UNV cannot drive code.",
            },
            "url": {"type": "string", "description": "Official page for [DOC]"},
            "reason": {"type": "string", "description": "One-line reason"},
            "code_depends": {
                "type": "boolean",
                "description": "Whether shipped code will read this knob",
            },
        },
        "required": ["knob", "decision", "tag", "reason"],
    },
}

SCAFFOLD_PROFILE = {
    "name": "scaffold_profile",
    "description": (
        "When to call: after canvas and spec exist, to write agents/<name>/. "
        "Creates a validator-passing skeleton empty of research-bot and "
        "inception internals. No secrets."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Directory and distribution name",
            },
            "job": {
                "type": "string",
                "description": "One sentence: what it does and does not do",
            },
            "author": {"type": "string", "description": "distribution.yaml author"},
        },
        "required": ["name", "job"],
    },
}

CHECK_PROFILE = {
    "name": "check_profile",
    "description": (
        "When to call: after scaffold or before a review. Runs factory "
        "validator rules on one path. Returns JSON gaps."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to agents/<name>/ or an absolute profile dir",
            }
        },
        "required": ["path"],
    },
}

ALL = [DOCS_RESOLVE, DOCS_ASK, PROBE_KNOB, SCAFFOLD_PROFILE, CHECK_PROFILE]
