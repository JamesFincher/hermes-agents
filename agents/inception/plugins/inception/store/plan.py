"""Plan ledger and the shared check_plan gate.

One record per target profile name. evaluate_plan is the only completeness
check. The check_plan tool and the policy fence both call it.
"""

from __future__ import annotations

import re
from typing import Any

from ..runtime import (
    FORBIDDEN_CROSS_IDS,
    OUROBOROS_PLUGIN_NAMES,
    RESERVED_PROFILE_NAMES,
    find_repo_root,
)
from . import ledger

KINDS = frozenset({"tool", "skill", "mcp", "plugin", "hook", "config"})
REQUIRED_TRACKS = ("tool", "skill", "mcp", "plugin")
PATTERNS = (
    "intercept-and-distil",
    "fence",
    "free output",
    "ledger",
    "governor",
)
CONTEXT_ECONOMICS_KNOBS = (
    "compression.threshold",
    "threshold_tokens",
    "tail_mode",
    "protect_last_n",
    "protect_first_n",
    "in_place",
    "idle_compact_after_seconds",
    "proactive_prune_tokens",
    "proactive_prune_min_result_chars",
    "proactive_prune_min_reclaim_tokens",
    "tool_output.max_bytes",
    "tool_output.max_lines",
    "tool_output.max_line_length",
    "tool_budget.mcp_result_size_chars",
    "file_read_max_chars",
    "context_file_max_chars",
    "context.engine",
)
CANVAS_HEADINGS = (
    (1, "job"),
    (2, "who it beats"),
    (3, "mechanism"),
    (4, "loop"),
    (5, "scarce"),
    (6, "durable"),
    (7, "custom surface"),
    (8, "fan-out"),
    (9, "knob"),
    (10, "failure"),
    (11, "eval"),
    (12, "honest"),
)
SPEC_NEEDLES = (
    ("verdict", ("verdict",)),
    ("incumbent_mechanism_map", ("incumbent",)),
    ("load_bearing_inventions", ("load-bearing", "load bearing", "invention")),
    ("nine_surfaces", ("nine surface", "surface-by-surface", "surface by surface")),
    ("plugin_file_map", ("plugin file", "plugin map")),
    ("tool_schemas", ("tool schema", "full tool")),
    ("hook_table", ("hook table", "hooks")),
    ("data_schemas", ("data schema",)),
    ("skill_list", ("skill list", "skills")),
    ("mcp_list", ("mcp",)),
    ("delegation", ("delegation",)),
    ("token_economics", ("token",)),
    ("failure_ladder", ("failure ladder",)),
    ("eval_design", ("eval",)),
    ("phased_acceptance", ("p1", "phased", "acceptance")),
    ("honest_limits", ("honest limit",)),
)
SURFACE_SECTIONS = ("plugin", "tool", "skill", "mcp")
MIN_CANVAS_SECTION = 40
MIN_SPEC_SECTION = 80
MIN_SPEC_CHARS = 2500
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,47}$")


def empty_plan(name: str, job: str, incumbent: str, axis: str) -> dict[str, Any]:
    return {
        "name": name,
        "job": job,
        "incumbent": incumbent,
        "axis": axis,
        "started": True,
        "investigations": [],
        "canvas_path": "",
        "spec_path": "",
        "patterns": [],
        "knob_sweep": [],
        "check_ok": False,
        "gaps": [],
    }


def validate_target_name(name: str) -> str | None:
    if not name or not _NAME_RE.match(name):
        return "name must be lowercase letters, digits, and hyphens"
    if name in RESERVED_PROFILE_NAMES:
        return f"reserved profile name: {name}"
    if name in OUROBOROS_PLUGIN_NAMES:
        return f"ouroboros plugin-name collision: {name}"
    if name in FORBIDDEN_CROSS_IDS or name == "inception":
        return f"forbidden profile name: {name}"
    return None


def get_plan(name: str) -> dict[str, Any] | None:
    data = ledger.load_store()
    plans = data.get("plans")
    if not isinstance(plans, dict):
        return None
    row = plans.get(name)
    return dict(row) if isinstance(row, dict) else None


def upsert_plan(name: str, updates: dict[str, Any]) -> dict[str, Any]:
    with ledger._LOCK:
        data = ledger._read_unlocked()
        plans = data.get("plans")
        if not isinstance(plans, dict):
            plans = {}
        current = dict(plans.get(name) or {})
        current.update(updates)
        current["name"] = name
        plans[name] = current
        data["plans"] = plans
        ledger._write_unlocked(data)
        return dict(current)


def attach_knob(name: str, row: dict[str, Any]) -> None:
    plan = get_plan(name)
    if plan is None:
        return
    sweep = list(plan.get("knob_sweep") or [])
    sweep.append(dict(row))
    upsert_plan(name, {"knob_sweep": sweep})


def split_markdown_sections(markdown: str) -> list[tuple[str, str]]:
    text = markdown.replace("\r\n", "\n")
    parts = re.split(r"(?m)^##\s+", text)
    sections: list[tuple[str, str]] = []
    for part in parts[1:]:
        line, _, rest = part.partition("\n")
        sections.append((line.strip(), rest.strip()))
    return sections


def canvas_gaps(markdown: str) -> list[str]:
    gaps: list[str] = []
    if "# profile canvas" not in markdown.lower():
        gaps.append("canvas must start with a Profile canvas title")
    sections = split_markdown_sections(markdown)
    if len(sections) < 12:
        gaps.append(f"canvas must have all 12 §6 sections (found {len(sections)})")
    found_nums: set[int] = set()
    for heading, body in sections:
        match = re.match(r"(\d+)\.", heading)
        if match:
            found_nums.add(int(match.group(1)))
        if len(body) < MIN_CANVAS_SECTION:
            gaps.append(f"canvas section {heading!r} is empty or stub")
    for number, needle in CANVAS_HEADINGS:
        if number not in found_nums:
            matched = any(needle in heading.lower() for heading, _ in sections)
            if not matched:
                gaps.append(f"canvas missing §6 section {number} ({needle})")
    return gaps


def spec_gaps(markdown: str) -> list[str]:
    gaps: list[str] = []
    if len(markdown.strip()) < MIN_SPEC_CHARS:
        gaps.append(
            f"spec is a stub ({len(markdown.strip())} chars; need {MIN_SPEC_CHARS}+)"
        )
    lowered = markdown.lower()
    sections = split_markdown_sections(markdown)
    headings = " ".join(heading.lower() for heading, _ in sections)
    for key, needles in SPEC_NEEDLES:
        if not any(needle in headings or needle in lowered for needle in needles):
            gaps.append(f"spec missing {key} section")
    for surface in SURFACE_SECTIONS:
        has_heading = any(surface in heading.lower() for heading, _ in sections)
        if not has_heading:
            gaps.append(f"spec missing {surface} section")
    for heading, body in sections:
        if len(body) < MIN_SPEC_SECTION:
            gaps.append(f"spec section {heading!r} is empty or stub")
    for tag in ("[DOC]", "[INF]", "[UNV]"):
        if tag not in markdown:
            gaps.append(f"spec must tag platform claims with {tag}")
    eval_body = ""
    for heading, body in sections:
        if "eval" in heading.lower():
            eval_body = body.lower()
            break
    if eval_body:
        if not re.search(r"\b([8-9]|1[0-9]|eight)\b", eval_body):
            gaps.append("spec eval must design 8+ frozen tasks")
        if "adversarial" not in eval_body:
            gaps.append("spec eval must include 2 adversarial tasks")
    incumbent_body = ""
    for heading, body in sections:
        if "incumbent" in heading.lower() or "mechanism" in heading.lower():
            incumbent_body += "\n" + body
    rows = [
        line
        for line in incumbent_body.splitlines()
        if line.strip().startswith("|") and "---" not in line and "mechanism" not in line.lower()
    ]
    if incumbent_body and len(rows) < 5:
        gaps.append("spec incumbent mechanism map needs 5–10 rows")
    return gaps


def _knob_hits(recorded: list[str], needed: str) -> bool:
    target = needed.lower()
    for item in recorded:
        value = item.lower()
        if target == value or value.endswith(target) or target.endswith(value):
            return True
        if target in value:
            return True
    return False


def _collect_knobs(plan: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for row in plan.get("knob_sweep") or []:
        if isinstance(row, dict) and row.get("knob"):
            found.append(str(row["knob"]))
    for row in plan.get("investigations") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("kind") or "") == "config" and row.get("question"):
            found.append(str(row.get("mapping") or row.get("question")))
    data = ledger.load_store()
    for row in data.get("probes") or []:
        if isinstance(row, dict) and row.get("knob"):
            if row.get("plan") == plan.get("name"):
                found.append(str(row["knob"]))
    return found


def _named_patterns(plan: dict[str, Any], blob: str) -> list[str]:
    named: list[str] = []
    explicit = plan.get("patterns") or []
    hay = blob.lower() + " " + " ".join(str(item) for item in explicit).lower()
    aliases = {
        "intercept-and-distil": ("intercept-and-distil", "intercept and distil"),
        "fence": ("fence",),
        "free output": ("free output", "free-output"),
        "ledger": ("ledger",),
        "governor": ("governor",),
    }
    for pattern, needles in aliases.items():
        if any(needle in hay for needle in needles):
            named.append(pattern)
    return named


def _unv_code_depends(plan: dict[str, Any]) -> bool:
    rows: list[dict[str, Any]] = []
    for bucket in ("investigations", "knob_sweep"):
        for row in plan.get(bucket) or []:
            if isinstance(row, dict):
                rows.append(row)
    data = ledger.load_store()
    for row in data.get("probes") or []:
        if isinstance(row, dict) and row.get("plan") == plan.get("name"):
            rows.append(row)
    for row in rows:
        tag = str(row.get("tag") or "").upper()
        if tag == "UNV" and bool(row.get("code_depends")):
            return True
    return False


def _forbidden_gaps(blob: str) -> list[str]:
    gaps: list[str] = []
    lowered = blob.lower()
    shared = "ar" + "my"
    if f"{shared}-runtime" in lowered or f"{shared}_runtime" in lowered:
        gaps.append("plan must not introduce a shared runtime layer")
    if re.search(r"from\s+hdr\s+import|\bimport\s+hdr\b", blob):
        gaps.append("plan must not import hdr")
    if re.search(r"hermes\s+plugins\s+doctor|\bplugins doctor\b", lowered):
        if not re.search(r"do not|don't|never|invent|reject|no official|not ship", lowered):
            gaps.append("plan must not invent plugins doctor")
    if "repo-root distribution.yaml" in lowered or "repo root distribution.yaml" in lowered:
        if "[unv]" not in lowered and "do not" not in lowered and "not ship" not in lowered:
            gaps.append("plan must not ship a repo-root distribution.yaml")
    return gaps


def _read_doc(path_str: str) -> str:
    if not path_str:
        return ""
    from pathlib import Path

    path = Path(path_str)
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def evaluate_plan(name: str) -> dict[str, Any]:
    gaps: list[str] = []
    target = str(name or "").strip().lower()
    if not target:
        return {"ok": False, "name": "", "gaps": ["name is required"]}
    problem = validate_target_name(target)
    if problem:
        return {"ok": False, "name": target, "gaps": [problem]}
    plan = get_plan(target)
    if plan is None or not plan.get("started"):
        return {
            "ok": False,
            "name": target,
            "gaps": ["plan_start was not called for this name"],
        }
    root = find_repo_root()
    canvas_path = str(plan.get("canvas_path") or "")
    spec_path = str(plan.get("spec_path") or "")
    if root is not None:
        default_canvas = root / "docs" / "profiles" / f"{target}-canvas.md"
        default_spec = root / "docs" / "profiles" / f"{target}-spec.md"
        if not canvas_path and default_canvas.is_file():
            canvas_path = str(default_canvas)
        if not spec_path and default_spec.is_file():
            spec_path = str(default_spec)
    canvas_text = _read_doc(canvas_path)
    spec_text = _read_doc(spec_path)
    if not canvas_text:
        gaps.append("canvas file is missing")
    else:
        gaps.extend(canvas_gaps(canvas_text))
    if not spec_text:
        gaps.append("spec file is missing")
    else:
        gaps.extend(spec_gaps(spec_text))
    investigations = [
        row for row in (plan.get("investigations") or []) if isinstance(row, dict)
    ]
    by_kind: dict[str, list[dict[str, Any]]] = {kind: [] for kind in KINDS}
    for row in investigations:
        kind = str(row.get("kind") or "")
        if kind in by_kind:
            by_kind[kind].append(row)
    for track in REQUIRED_TRACKS:
        rows = by_kind.get(track) or []
        if not rows:
            gaps.append(f"investigation track {track!r} has no rows")
            continue
        if track in {"mcp", "plugin"}:
            for row in rows:
                decision = str(row.get("decision") or "accept")
                if decision == "reject" and not str(row.get("reason") or "").strip():
                    gaps.append(f"{track} reject needs a reason")
        if track == "tool":
            for row in rows:
                if not all(str(row.get(key) or "").strip() for key in ("q1", "q2", "q3")):
                    gaps.append("tool investigation needs the three questions before a tool")
    recorded = _collect_knobs(plan)
    missing_knobs = [knob for knob in CONTEXT_ECONOMICS_KNOBS if not _knob_hits(recorded, knob)]
    if missing_knobs:
        gaps.append("knob sweep missing §5 context-economics: " + ", ".join(missing_knobs))
    blob = "\n".join([canvas_text, spec_text, str(plan.get("patterns") or "")])
    named = _named_patterns(plan, blob)
    if len(named) < 3:
        gaps.append("name at least three of the five §4 patterns")
    if _unv_code_depends(plan):
        gaps.append("[UNV] must not set code_depends")
    gaps.extend(_forbidden_gaps(blob))
    unique = []
    for item in gaps:
        if item not in unique:
            unique.append(item)
    ok = not unique
    try:
        upsert_plan(target, {"check_ok": ok, "gaps": unique, "patterns": named})
    except Exception:
        pass
    return {
        "ok": ok,
        "name": target,
        "gaps": unique,
        "tracks": {track: len(by_kind.get(track) or []) for track in REQUIRED_TRACKS},
        "patterns": named,
        "canvas_path": canvas_path,
        "spec_path": spec_path,
    }
