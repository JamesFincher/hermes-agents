"""pre_tool_call: the enforcement point.

This hook is where "never hallucinate" stops being a request and becomes a
refusal. It is a policy hook, so on an internal error it fails CLOSED for the
gated writes and says why — the alternative is a fabricated citation reaching a
file that a human then relies on.
"""
from __future__ import annotations
import json, logging, os
from pathlib import Path
from ..store import matter as M, gates, bus, ledger as L
from ..runtime import setting, data_dir

log = logging.getLogger("lex.policy")

# Intercepted before the registry — a directive here would be ignored.
INTERCEPTED = {"todo", "memory", "session_search"}
WRITE_TOOLS = {"write_file", "patch"}
FETCH_TOOLS = {"web_extract", "browser_navigate"}
ALLOWED_ROOTS = ("drafts", "research", "memos", "authority", "exhibits", "notes")

UPL = (
    "This profile does not file, serve, appear, sign, or advise. It drafts and cites. "
    "Produce the document as work product for review; do not perform the act."
)
ACT_MARKERS = ("efile", "e-file", "pacer upload", "file with the court", "submit to the court",
               "serve on", "docket this", "sign and submit")


def _audit(entry: dict) -> None:
    try:
        with (data_dir() / "audit" / "policy.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


def _block(msg: str, why: str, tool: str) -> dict:
    _audit({"decision": "block", "tool": tool, "why": why})
    return {"action": "block", "message": msg}


def pre_tool_call(tool_name=None, args=None, task_id=None, **kwargs):
    args = args or {}
    if tool_name in INTERCEPTED:
        return None

    try:
        # 1. Acting as counsel — refuse regardless of tool.
        blob = json.dumps(args, default=str).lower()
        if tool_name in ("terminal", "execute_code", "send_message") and any(a in blob for a in ACT_MARKERS):
            return _block(UPL, "upl-act", tool_name)

        # 2. Dedupe fetches: the same URL never costs twice.
        if tool_name in FETCH_TOOLS:
            url = bus.canonical_url(args.get("url", ""))
            if url:
                for a in L.search():
                    if a.get("canonical_url") == url and a.get("sha"):
                        return _block(
                            f"Already retrieved as {a['id']}. Use authority_read "
                            f"auth_id={a['id']} instead of fetching it again.",
                            "dedupe", tool_name)

        # 3. Write gate.
        if tool_name in WRITE_TOOLS:
            path = args.get("path") or args.get("file_path") or ""
            norm = os.path.normpath(path).lstrip("./")
            if norm.startswith("..") or os.path.isabs(norm):
                return _block(f"Writes are confined to {', '.join(ALLOWED_ROOTS)}/ inside the "
                              f"workspace. '{path}' is outside.", "path-escape", tool_name)
            if not any(norm.startswith(r + os.sep) or norm.startswith(r + "/") for r in ALLOWED_ROOTS):
                return _block(f"Writes are confined to {', '.join(ALLOWED_ROOTS)}/. "
                              f"Put this at drafts/{Path(norm).name}.", "path-root", tool_name)

            content = args.get("content") or args.get("new_string") or ""
            if len(content) < 40:
                return None
            m = M.load()
            if not m:
                return _block("No active matter. Jurisdiction and the fact table gate every "
                              "draft — run matter_open first.", "no-matter", tool_name)
            report = gates.run_all(content, m["matter_id"])
            if not report["pass"]:
                return _block(gates.block_message(report), "gates:" + ",".join(report["blocking"]),
                              tool_name)
            _audit({"decision": "allow", "tool": tool_name, "path": norm,
                    "citations": len(report["citation"]["citations"]),
                    "placeholders": report["fact"]["placeholders"]})
        return None

    except Exception as e:  # noqa: BLE001
        log.exception("policy hook error")
        if tool_name in WRITE_TOOLS:
            # Fail CLOSED on the gated path. A silent pass here is the failure
            # mode this whole profile exists to prevent.
            return _block(
                f"Gate could not be evaluated ({type(e).__name__}). Refusing the write. "
                "Run draft_check explicitly and report the error.", "gate-error", tool_name)
        return None
