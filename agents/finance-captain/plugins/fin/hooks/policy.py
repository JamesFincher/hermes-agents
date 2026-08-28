"""pre_tool_call: where the gates stop being advice.

Fails CLOSED on the report-write path and on anything that touches money.
"""
from __future__ import annotations
import json, logging, os
from pathlib import Path
from ..store import entity as E, gates, audit, mutations as MU
from ..runtime import setting

log = logging.getLogger("fin.policy")

INTERCEPTED = {"todo", "memory", "session_search"}
WRITE_TOOLS = {"write_file", "patch"}
ALLOWED_ROOTS = ("reports", "analysis", "exports", "notes", "working")

# Direct writes to money systems must not happen outside mutation_propose/apply.
MONEY_HINTS = ("payment", "payout", "transfer", "wire", "ach", "pay_bill", "refund",
               "payroll", "charge", "invoice.send", "bill.pay")
ADVICE_HINTS = ("should i buy", "should we buy", "investment advice", "tax advice",
                "file our taxes", "which stock", "portfolio allocation")


def _block(msg, why, tool):
    audit.write("policy", {"decision": "block", "tool": tool, "why": why})
    return {"action": "block", "message": msg}


def pre_tool_call(tool_name=None, args=None, task_id=None, **kwargs):
    args = args or {}
    if tool_name in INTERCEPTED:
        return None
    try:
        blob = json.dumps(args, default=str).lower()

        # 1. Money-touching calls must go through the mutation pipeline.
        if tool_name and tool_name.startswith("mcp_") and any(h in blob for h in MONEY_HINTS):
            return _block(
                "Direct calls to money-moving endpoints are not permitted. Use "
                "mutation_propose, show the proposal to a human, get approval for that "
                "specific proposal id, then mutation_apply.", "direct-money-call", tool_name)

        # 2. Advice boundary.
        if any(h in blob for h in ADVICE_HINTS):
            return _block(
                "This profile prepares and reports; it does not give investment, tax, or "
                "securities advice. Produce the analysis and the numbers, and route the "
                "decision to a CPA, tax advisor, or licensed adviser.", "advice-boundary", tool_name)

        # 3. Report/file write gate.
        if tool_name in WRITE_TOOLS:
            path = args.get("path") or args.get("file_path") or ""
            norm = os.path.normpath(path).lstrip("./")
            if norm.startswith("..") or os.path.isabs(norm):
                return _block(f"Writes are confined to {', '.join(ALLOWED_ROOTS)}/. "
                              f"'{path}' is outside.", "path-escape", tool_name)
            if not any(norm.startswith(r + "/") or norm == r for r in ALLOWED_ROOTS):
                return _block(f"Writes are confined to {', '.join(ALLOWED_ROOTS)}/. "
                              f"Put this at reports/{Path(norm).name}.", "path-root", tool_name)

            content = args.get("content") or args.get("new_string") or ""
            if len(content) < 60:
                return None
            e = E.load()
            if not e:
                return _block("No active entity. Currency and basis gate every number — "
                              "run entity_open first.", "no-entity", tool_name)
            rep = gates.run_all(content)
            if not rep["pass"]:
                return _block(gates.block_message(rep), "gates:" + ",".join(rep["blocking"]),
                              tool_name)
            audit.write("policy", {"decision": "allow", "tool": tool_name, "path": norm,
                                   "numbers_checked": rep["numbers"]["numbers_checked"]})
        return None

    except Exception as ex:  # noqa: BLE001
        log.exception("policy hook error")
        if tool_name in WRITE_TOOLS:
            return _block(f"Gate could not be evaluated ({type(ex).__name__}). Refusing the "
                          "write. Run report_check explicitly and report the error.",
                          "gate-error", tool_name)
        return None
