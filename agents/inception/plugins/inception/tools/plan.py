"""Plan-phase tools the inception plugin registers.

json.dumps strings. Never raise. Do not clone hdr names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..runtime import dump, error, find_repo_root
from ..store import ledger, plan as plan_store


def plan_start(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        name = str(payload.get("name") or "").strip().lower()
        job = str(payload.get("job") or "").strip()
        incumbent = str(payload.get("incumbent") or "").strip()
        axis = str(payload.get("axis") or "").strip()
        if not name or not job or not incumbent or not axis:
            return error("name, job, incumbent, and axis are required")
        problem = plan_store.validate_target_name(name)
        if problem:
            return error(problem)
        existing = plan_store.get_plan(name)
        row = plan_store.empty_plan(name, job, incumbent, axis)
        if existing and existing.get("started"):
            row["investigations"] = list(existing.get("investigations") or [])
            row["canvas_path"] = existing.get("canvas_path") or ""
            row["spec_path"] = existing.get("spec_path") or ""
            row["patterns"] = list(existing.get("patterns") or [])
            row["knob_sweep"] = list(existing.get("knob_sweep") or [])
            row["job"] = job
            row["incumbent"] = incumbent
            row["axis"] = axis
        saved = plan_store.upsert_plan(name, row)
        ledger.add_audit("plan_start", name)
        return dump({"ok": True, "plan": saved})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def investigate_surface(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        name = str(payload.get("name") or "").strip().lower()
        kind = str(payload.get("kind") or "").strip().lower()
        question = str(payload.get("question") or "").strip()
        evidence = str(payload.get("evidence") or "").strip()
        tag = str(payload.get("tag") or "").strip().upper()
        mapping = str(payload.get("mapping") or "").strip()
        url = str(payload.get("url") or "").strip()
        decision = str(payload.get("decision") or "").strip().lower()
        reason = str(payload.get("reason") or "").strip()
        code_depends = bool(payload.get("code_depends") or False)
        q1 = str(payload.get("q1") or "").strip()
        q2 = str(payload.get("q2") or "").strip()
        q3 = str(payload.get("q3") or "").strip()
        if not name:
            return error("name is required")
        current = plan_store.get_plan(name)
        if current is None or not current.get("started"):
            return error("plan_start was not called for this name")
        if kind not in plan_store.KINDS:
            return error("kind must be tool, skill, mcp, plugin, hook, or config")
        if not question or not evidence or not mapping or not tag:
            return error("question, evidence, mapping, and tag are required")
        if tag not in {"DOC", "INF", "UNV"}:
            return error("tag must be DOC, INF, or UNV")
        if tag == "DOC" and not url.startswith("https://"):
            return error("[DOC] requires an official https URL")
        if tag == "UNV" and code_depends:
            return error("code must not depend on [UNV]")
        if kind == "tool" and not (q1 and q2 and q3):
            return error("kind=tool requires q1, q2, q3 (three questions before a tool)")
        if kind in {"mcp", "plugin"} and decision == "reject" and not reason:
            return error(f"{kind} reject needs a reason")
        row = {
            "kind": kind,
            "question": question,
            "evidence": evidence,
            "tag": tag,
            "url": url,
            "mapping": mapping,
            "decision": decision or "accept",
            "reason": reason,
            "code_depends": code_depends,
            "q1": q1,
            "q2": q2,
            "q3": q3,
        }
        investigations = list(current.get("investigations") or [])
        investigations.append(row)
        saved = plan_store.upsert_plan(name, {"investigations": investigations})
        ledger.add_audit("investigate_surface", f"{name}:{kind}")
        return dump({"ok": True, "investigation": row, "count": len(investigations), "plan": name})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def write_canvas(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        name = str(payload.get("name") or "").strip().lower()
        markdown = str(payload.get("markdown") or "").strip()
        if not name or not markdown:
            return error("name and markdown are required")
        current = plan_store.get_plan(name)
        if current is None or not current.get("started"):
            return error("plan_start was not called for this name")
        gaps = plan_store.canvas_gaps(markdown)
        if gaps:
            return error("canvas refused: " + "; ".join(gaps))
        root = find_repo_root()
        if root is None:
            return error("library root not found (docs/PROFILE-PLAYBOOK.md missing)")
        dest = root / "docs" / "profiles" / f"{name}-canvas.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(markdown if markdown.endswith("\n") else markdown + "\n", encoding="utf-8")
        named = plan_store._named_patterns(current, markdown)
        plan_store.upsert_plan(
            name,
            {"canvas_path": str(dest), "patterns": named},
        )
        ledger.add_audit("write_canvas", str(dest))
        return dump({"ok": True, "path": str(dest), "patterns": named})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def write_spec(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        name = str(payload.get("name") or "").strip().lower()
        markdown = str(payload.get("markdown") or "").strip()
        if not name or not markdown:
            return error("name and markdown are required")
        current = plan_store.get_plan(name)
        if current is None or not current.get("started"):
            return error("plan_start was not called for this name")
        root = find_repo_root()
        if root is None:
            return error("library root not found (docs/PROFILE-PLAYBOOK.md missing)")
        canvas = root / "docs" / "profiles" / f"{name}-canvas.md"
        stored = str(current.get("canvas_path") or "")
        stored_ok = bool(stored) and Path(stored).is_file()
        if not canvas.is_file() and not stored_ok:
            return error("write_spec fails until the canvas exists")
        gaps = plan_store.spec_gaps(markdown)
        if gaps:
            return error("spec refused: " + "; ".join(gaps))
        dest = root / "docs" / "profiles" / f"{name}-spec.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(markdown if markdown.endswith("\n") else markdown + "\n", encoding="utf-8")
        named = plan_store._named_patterns(current, markdown)
        merged = list(dict.fromkeys(list(current.get("patterns") or []) + named))
        plan_store.upsert_plan(name, {"spec_path": str(dest), "patterns": merged})
        ledger.add_audit("write_spec", str(dest))
        return dump({"ok": True, "path": str(dest), "patterns": merged})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))


def check_plan(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        name = str(payload.get("name") or "").strip().lower()
        if not name:
            return error("name is required")
        return dump(plan_store.evaluate_plan(name))
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
