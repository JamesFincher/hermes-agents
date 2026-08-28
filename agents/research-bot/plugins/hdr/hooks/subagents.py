"""subagent_start / subagent_stop reconciliation."""

from __future__ import annotations

from typing import Any

from ..store import bus, run


def subagent_start(
    subagent_id: str = "",
    task: str = "",
    **kwargs: Any,
) -> None:
    try:
        child_id = str(subagent_id or kwargs.get("task_id") or "unknown")
        open_question = str(kwargs.get("open_question") or task or "")

        def _apply(current: dict[str, Any]) -> None:
            children = current.setdefault("children", {})
            children[child_id] = {
                "status": "running",
                "task": task or kwargs.get("goal") or "",
                "open_question": open_question,
            }

        updated = run.mutate_run(_apply)
        if updated:
            bus.append_audit(updated.get("run_id") or "", {"event": "subagent_start", "id": subagent_id})
    except Exception:
        return


def subagent_stop(
    subagent_id: str = "",
    error: str | None = None,
    **kwargs: Any,
) -> None:
    try:
        child_id = str(subagent_id or "unknown")
        mandate = ""

        def _apply(current: dict[str, Any]) -> None:
            nonlocal mandate
            children = current.setdefault("children", {})
            node = children.setdefault(child_id, {})
            node["status"] = "failed" if error else "done"
            if error:
                node["error"] = str(error)
            node["tool_calls"] = kwargs.get("tool_calls")
            mandate = str(node.get("open_question") or kwargs.get("open_question") or "")

        updated = run.mutate_run(_apply)
        if mandate:
            run.mark_mandate(mandate, "failed" if error else "answered")
        if updated:
            bus.append_audit(
                updated.get("run_id") or "",
                {"event": "subagent_stop", "id": subagent_id, "error": error},
            )
    except Exception:
        return
