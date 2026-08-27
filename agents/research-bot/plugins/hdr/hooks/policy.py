"""pre_tool_call: dedupe fence, write allowlist, Citation Gate, budget."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..runtime import (
    BRIEF_DIRS,
    DOMAIN_SOFT_CAP,
    INTERCEPTED,
    NETWORK_TOOLS,
    READ_ONLY_WHEN_HARD,
    TERMINAL_TOOLS,
    WRITE_TOOLS,
    setting,
)
from ..store import bus, ledger, run

_SID_RE = re.compile(r"\[S(\d+)\]")
_STAT_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\b(19|20)\d{2}\b|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|“[^”]{3,}”|\"[^\"]{3,}\")"
)
_CURL_SH = re.compile(r"curl\b[^|\n]*\|\s*(?:ba)?sh\b", re.I)
_CRED = re.compile(r"(~/?\.ssh|/etc/shadow|\.env\b|auth\.json|id_rsa)", re.I)
_SCAFFOLD = re.compile(r"\b(git\s+init|npm\s+init|pip\s+install|apt-get)\b", re.I)
_REDIRECT = re.compile(r"(?:>>?|tee)\s+(\S+)")
_QUERY_WINDOW_S = 15 * 60


def pre_tool_call(
    tool_name: str,
    args: dict[str, Any],
    task_id: str = "",
    **kwargs: Any,
) -> dict[str, Any] | None:
    del task_id, kwargs
    try:
        name = str(tool_name or "")
        payload = args if isinstance(args, dict) else {}
        if name in INTERCEPTED and name != "delegate_task":
            if name == "memory":
                current = run.load_run()
                bus.append_audit(
                    (current or {}).get("run_id") or "",
                    {"event": "memory-observe", "note": "findings belong in the ledger"},
                )
            return None
        current = run.load_run()
        governor = (current or {}).get("governor") or "GREEN"
        if name == "delegate_task":
            blocked = _delegate_fence(payload, current, governor)
            if blocked:
                return blocked
        blocked = _budget_fence(name, governor)
        if blocked:
            return blocked
        blocked = _dedupe_fence(name, payload)
        if blocked:
            return blocked
        blocked = _domain_soft_cap(name, payload, current)
        if blocked:
            return blocked
        if name in WRITE_TOOLS:
            blocked = _write_allowlist(payload)
            if blocked:
                return blocked
            blocked = _citation_gate(payload)
            if blocked:
                return blocked
        if name in TERMINAL_TOOLS:
            blocked = _terminal_effect(payload)
            if blocked:
                return blocked
        return None
    except Exception:
        return None


def post_tool_call(
    tool_name: str,
    args: dict[str, Any],
    result: str,
    task_id: str = "",
    duration_ms: int = 0,
    **kwargs: Any,
) -> None:
    del args, result, task_id, kwargs
    try:
        current = run.load_run()
        bus.append_audit(
            (current or {}).get("run_id") or "",
            {"tool": tool_name, "duration_ms": duration_ms},
        )
        if tool_name in NETWORK_TOOLS:
            run.add_spend(fetches=1)
    except Exception:
        return


def _named_gaps(current: dict[str, Any] | None) -> list[str]:
    if not current:
        return []
    gaps = list(current.get("named_gaps") or [])
    if not gaps:
        gaps = list(current.get("open_questions") or [])
    return [str(item) for item in gaps if str(item).strip()]


def _matches_named_gap(text: str, gaps: list[str]) -> bool:
    blob = (text or "").lower()
    if not blob or not gaps:
        return False
    for gap in gaps:
        needle = gap.strip().lower()
        if not needle:
            continue
        if needle in blob or blob[:80] in needle:
            return True
        if len(needle) >= 12 and needle[:40] in blob:
            return True
    return False


def _delegate_fence(
    args: dict[str, Any],
    current: dict[str, Any] | None,
    governor: str,
) -> dict[str, Any] | None:
    if governor == "GREEN":
        return None
    if governor in {"RED", "HARD"}:
        return {
            "action": "block",
            "message": f"Governor {governor}: no new delegate_task. Synthesize from the ledger.",
        }
    goal = str(
        args.get("goal")
        or args.get("prompt")
        or args.get("task")
        or args.get("instruction")
        or ""
    )
    if _matches_named_gap(goal, _named_gaps(current)):
        return None
    return {
        "action": "block",
        "message": (
            "Governor AMBER: no new delegate_task batches. "
            "Depth on a named gap only."
        ),
    }


def _budget_fence(tool_name: str, governor: str) -> dict[str, Any] | None:
    if governor == "GREEN":
        return None
    if governor == "RED" and tool_name in NETWORK_TOOLS:
        return {
            "action": "block",
            "message": "Governor RED: block network tools. Synthesize now from the ledger.",
        }
    if governor == "HARD" and tool_name not in READ_ONLY_WHEN_HARD:
        return {
            "action": "block",
            "message": "Governor HARD: only ledger tools and brief-path writes remain.",
        }
    return None


def _dedupe_fence(tool_name: str, args: dict[str, Any]) -> dict[str, Any] | None:
    if tool_name not in {"web_extract", "browser_navigate"}:
        if tool_name == "web_search":
            return _query_dedupe(args)
        return None
    url = str(args.get("url") or args.get("target") or "")
    if not url:
        return None
    canonical = bus.canonicalize(url)
    existing = bus.corpus_exists_for_url(canonical)
    if existing:
        sid = existing.get("id")
        return {
            "action": "block",
            "message": (
                f"Already retrieved as {sid} — read_file {existing.get('corpus')} "
                f"or call evidence_read src={sid}"
            ),
        }
    return None


def _query_dedupe(args: dict[str, Any]) -> dict[str, Any] | None:
    query = str(args.get("query") or args.get("q") or "").strip().lower()
    if not query:
        return None
    current = run.load_run()
    if not current:
        return None
    seen = current.setdefault("query_hashes", {})
    key = re.sub(r"\s+", " ", query)
    now = time.time()
    prior = seen.get(key)
    if isinstance(prior, (int, float)) and now - float(prior) < _QUERY_WINDOW_S:
        return {
            "action": "block",
            "message": f"Near-duplicate search in the last 15 minutes: {key[:80]}",
        }
    seen[key] = now
    run.save_run(current)
    return None


def _domain_soft_cap(
    tool_name: str,
    args: dict[str, Any],
    current: dict[str, Any] | None,
) -> dict[str, Any] | None:
    denylist = setting("domain_denylist", []) or []
    url = str(args.get("url") or "")
    host = ""
    if url:
        host = (urlparse(url).hostname or "").lower()
    if host and isinstance(denylist, list) and host in denylist:
        return {"action": "block", "message": f"domain denylist: {host}"}
    if tool_name != "web_search" or not current:
        return None
    counts = current.get("domain_counts") or {}
    if not isinstance(counts, dict):
        return None
    saturated = [
        str(name)
        for name, count in counts.items()
        if isinstance(count, (int, float)) and int(count) >= DOMAIN_SOFT_CAP and str(name)
    ]
    if not saturated:
        return None
    key = "query" if "query" in args or "q" not in args else "q"
    query = str(args.get(key) or args.get("query") or args.get("q") or "")
    extra = [
        f"-site:{name}"
        for name in saturated[:8]
        if f"-site:{name}" not in query
    ]
    if not extra:
        return None
    return {"action": "modify", "args": {key: (query + " " + " ".join(extra)).strip()}}


def _path_allowed(raw: str) -> bool:
    try:
        path = Path(raw)
    except Exception:
        return False
    parts = set(path.parts)
    return bool(parts & BRIEF_DIRS)


def _write_allowlist(args: dict[str, Any]) -> dict[str, Any] | None:
    path = str(args.get("path") or args.get("file") or args.get("target") or "")
    if not path:
        return None
    if _path_allowed(path):
        return None
    return {
        "action": "block",
        "message": (
            f"Write allowlist: {path} is outside notes/ research/ briefs/ "
            "findings/ citations/ sources/ data/."
        ),
    }


def _citation_gate(args: dict[str, Any]) -> dict[str, Any] | None:
    path = str(args.get("path") or args.get("file") or "")
    if not _path_allowed(path):
        return None
    content = str(args.get("content") or args.get("new_string") or args.get("text") or "")
    if not content.strip():
        return None
    sources = {str(src.get("id")) for src in ledger.list_sources()}
    offenders: list[str] = []
    for match in _SID_RE.finditer(content):
        sid = f"S{match.group(1)}"
        if sid not in sources:
            offenders.append(f"unresolvable {sid}")
    for sentence in re.split(r"(?<=[.!?])\s+", content):
        if _STAT_RE.search(sentence) and not _SID_RE.search(sentence):
            offenders.append(sentence.strip()[:180])
    if offenders:
        return {
            "action": "block",
            "message": "Citation Gate refused this brief:\n- " + "\n- ".join(offenders[:8]),
        }
    return None


def _terminal_effect(args: dict[str, Any]) -> dict[str, Any] | None:
    command = str(
        args.get("command") or args.get("cmd") or args.get("code") or args.get("script") or ""
    )
    if not command:
        return None
    if _CURL_SH.search(command):
        return {"action": "block", "message": "Blocked: curl piped to a shell."}
    if _CRED.search(command):
        return {"action": "block", "message": "Blocked: credential-file read."}
    for match in _REDIRECT.finditer(command):
        target = match.group(1).strip("'\"")
        if target.startswith("/dev/"):
            continue
        if not _path_allowed(target) and not target.startswith("research/") and "/" in target:
            if not any(part in target for part in BRIEF_DIRS):
                return {
                    "action": "block",
                    "message": f"Blocked: outbound write outside allowlist ({target}).",
                }
    if _SCAFFOLD.search(command):
        current = run.load_run()
        bus.append_audit(
            (current or {}).get("run_id") or "",
            {"event": "scaffold-warning", "command": command[:200]},
        )
    return None
