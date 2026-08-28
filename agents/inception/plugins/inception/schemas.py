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
            "name": {
                "type": "string",
                "description": "Optional target profile. Attaches this probe to that plan.",
            },
        },
        "required": ["knob", "decision", "tag", "reason"],
    },
}

PLAN_START = {
    "name": "plan_start",
    "description": (
        "When to call: first. Opens the plan ledger for one target name. "
        "Requires job, incumbent, and axis. Does not write agents/<name>/."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Target profile directory name"},
            "job": {"type": "string", "description": "What it does and does not do"},
            "incumbent": {"type": "string", "description": "Named product or workflow to beat"},
            "axis": {"type": "string", "description": "The one axis of comparison"},
        },
        "required": ["name", "job", "incumbent", "axis"],
    },
}

INVESTIGATE_SURFACE = {
    "name": "investigate_surface",
    "description": (
        "When to call: after plan_start, once per surface question. "
        "kind is tool, skill, mcp, plugin, hook, or config. Records "
        "Context7 or official evidence, a [DOC]/[INF]/[UNV] tag, and "
        "the §3 mapping. kind=tool needs q1 q2 q3."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Target profile name"},
            "kind": {
                "type": "string",
                "enum": ["tool", "skill", "mcp", "plugin", "hook", "config"],
                "description": "Which of the four tracks plus hook or config",
            },
            "question": {"type": "string", "description": "What this row asks"},
            "evidence": {"type": "string", "description": "Context7 or official quote"},
            "tag": {
                "type": "string",
                "enum": ["DOC", "INF", "UNV"],
                "description": "DOC needs a url. UNV cannot drive code.",
            },
            "mapping": {"type": "string", "description": "§3 decision-tree landing"},
            "url": {"type": "string", "description": "Official page for [DOC]"},
            "decision": {
                "type": "string",
                "enum": ["accept", "reject", "default"],
                "description": "mcp and plugin may reject with a reason",
            },
            "reason": {"type": "string", "description": "Required when decision is reject"},
            "code_depends": {"type": "boolean", "description": "Whether shipped code will read this"},
            "q1": {"type": "string", "description": "Tool Q1: would a skill plus an existing tool do?"},
            "q2": {"type": "string", "description": "Tool Q2: called more than twice per run?"},
            "q3": {"type": "string", "description": "Tool Q3: can output be wrong undetected?"},
        },
        "required": ["name", "kind", "question", "evidence", "tag", "mapping"],
    },
}

WRITE_CANVAS = {
    "name": "write_canvas",
    "description": (
        "When to call: after the four investigation tracks. Writes "
        "docs/profiles/<name>-canvas.md. All 12 playbook §6 sections "
        "must be filled. Refuses empty sections."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Target profile name"},
            "markdown": {"type": "string", "description": "Full canvas with all 12 §6 headings"},
        },
        "required": ["name", "markdown"],
    },
}

WRITE_SPEC = {
    "name": "write_spec",
    "description": (
        "When to call: after write_canvas. Writes docs/profiles/<name>-spec.md "
        "at counsel and HDR depth. Refuses a stub. Fails if the canvas is missing."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Target profile name"},
            "markdown": {"type": "string", "description": "Full spec. Not a stub."},
        },
        "required": ["name", "markdown"],
    },
}

CHECK_PLAN = {
    "name": "check_plan",
    "description": (
        "When to call: before scaffold_profile. Returns JSON gaps. "
        "ok only when canvas, spec, four tracks, §5 context-economics, "
        "and three §4 patterns are complete."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Target profile name"},
        },
        "required": ["name"],
    },
}

SCAFFOLD_PROFILE = {
    "name": "scaffold_profile",
    "description": (
        "When to call: after check_plan returns ok. Writes agents/<name>/. "
        "Hard-fails without a complete plan. Creates a validator-passing "
        "skeleton empty of research-bot and inception internals. No secrets."
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

ALL = [
    DOCS_RESOLVE,
    DOCS_ASK,
    PROBE_KNOB,
    PLAN_START,
    INVESTIGATE_SURFACE,
    WRITE_CANVAS,
    WRITE_SPEC,
    CHECK_PLAN,
    SCAFFOLD_PROFILE,
    CHECK_PROFILE,
]
