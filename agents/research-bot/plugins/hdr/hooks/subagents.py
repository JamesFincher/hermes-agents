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
        current = run.load_run()
        if not current:
            return
        children = current.setdefault("children", {})
        children[str(subagent_id or kwargs.get("task_id") or "unknown")] = {
            "status": "running",
            "task": task or kwargs.get("goal") or "",
            "open_question": kwargs.get("open_question") or task,
        }
        run.save_run(current)
        bus.append_audit(current.get("run_id") or "", {"event": "subagent_start", "id": subagent_id})
    except Exception:
        return


def subagent_stop(
    subagent_id: str = "",
    error: str | None = None,
    **kwargs: Any,
) -> None:
    try:
        current = run.load_run()
        if not current:
            return
        children = current.setdefault("children", {})
        node = children.setdefault(str(subagent_id or "unknown"), {})
        node["status"] = "failed" if error else "done"
        if error:
            node["error"] = str(error)
        node["tool_calls"] = kwargs.get("tool_calls")
        run.save_run(current)
        bus.append_audit(
            current.get("run_id") or "",
            {"event": "subagent_stop", "id": subagent_id, "error": error},
        )
    except Exception:
        return
