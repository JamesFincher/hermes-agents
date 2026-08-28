"""pre_tool_call: dedupe fence, write allowlist, Citation Gate, budget."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..runtime import (
    BRIEF_DIRS,
    CITATION_GATE_DIRS,
    DOMAIN_SOFT_CAP,
    INTERCEPTED,
    NETWORK_TOOLS,
    READ_ONLY_WHEN_HARD,
    RED_EGRESS_TOOLS,
    TERMINAL_TOOLS,
    WRITE_TOOLS,
    estimate_tokens,
    setting,
)
from ..store import bus, ledger, run
from ..tools.citation import claim_verify

_SID_RE = re.compile(r"\[S(\d+)\]")
_STAT_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\b(19|20)\d{2}\b|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|“[^”]{3,}”|\"[^\"]{3,}\")"
)
_CURL_SH = re.compile(r"curl\b[^|\n]*\|\s*(?:ba)?sh\b", re.I)
_CRED = re.compile(r"(~/?\.ssh|/etc/shadow|\.env\b|auth\.json|id_rsa)", re.I)
_PKG_INSTALL = re.compile(r"\b(pip\s+install|npm\s+i(?:nstall)?\b|apt-get\s+install)\b", re.I)
_SCAFFOLD = re.compile(r"\b(git\s+init|npm\s+init)\b", re.I)
_REDIRECT = re.compile(r"(?:>>?|tee)\s+(\S+)")
_OPEN_WRITE = re.compile(
    r"""open\s*\(\s*(['"])(?P<path>[^'"]+)\1\s*,\s*(['"])(?P<mode>[^'"]*w[^'"]*)\3""",
    re.I,
)
_PATHLIB_WRITE = re.compile(
    r"""Path\s*\(\s*(['"])(?P<path>[^'"]+)\1\s*\)\s*\.\s*write_(?:text|bytes)\s*\(""",
)
_NET_CALL = re.compile(
    r"""(?:requests\.(?:get|post|put|delete|head|patch)|urllib\.request\.(?:urlopen|Request))\s*\(""",
    re.I,
)
_EGRESS = re.compile(
    r"\b(curl|wget|httpx?|requests\.|urllib|aiohttp|web_search|ftp\b|ncat|\bnc\b|ssh\b)\b"
    r"|https?://",
    re.I,
)
_QUERY_WINDOW_S = 15 * 60
_FAIL_CLOSED = WRITE_TOOLS | NETWORK_TOOLS | TERMINAL_TOOLS | {"delegate_task"}


def pre_tool_call(
    tool_name: str,
    args: dict[str, Any],
    task_id: str = "",
    **kwargs: Any,
) -> dict[str, Any] | None:
    del task_id, kwargs
    name = str(tool_name or "")
    payload = args if isinstance(args, dict) else {}
    try:
        result = _evaluate(name, payload)
        if result and result.get("action") in {"block", "modify"}:
            _log_policy(name, result, payload)
        return result
    except Exception:
        if name in _FAIL_CLOSED:
            blocked = {"action": "block", "message": "HDR policy error"}
            try:
                _log_policy(name, blocked, payload)
            except Exception:
                pass
            return blocked
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
    except Exception:
        return


def _evaluate(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if name in INTERCEPTED and name != "delegate_task":
        if name == "memory":
            current = run.load_run()
            bus.append_audit(
                (current or {}).get("run_id") or "",
                {"event": "memory-observe", "note": "findings belong in the ledger"},
            )
        return None
    current = run.load_run()
    if current:
        current = run.refresh_governor(current)
    governor = (current or {}).get("governor") or "GREEN"
    if (current or {}).get("phase") == "synthesis" and name in NETWORK_TOOLS:
        return {
            "action": "block",
            "message": "Phase SYNTHESIS: no network. Read the Evidence Bus.",
            "reason": "phase-synthesis",
        }
    if name == "delegate_task":
        blocked = _delegate_fence(payload, current, governor)
        if blocked:
            return {**blocked, "reason": "delegate-fence"}
    blocked = _budget_fence(name, payload, governor, current)
    if blocked:
        return {**blocked, "reason": "budget-fence"}
    blocked = _dedupe_fence(name, payload)
    if blocked:
        return {**blocked, "reason": "dedupe-fence"}
    blocked = _domain_soft_cap(name, payload, current)
    if blocked:
        return {**blocked, "reason": "domain-cap"}
    if name in WRITE_TOOLS:
        blocked = _write_allowlist(payload)
        if blocked:
            return {**blocked, "reason": "write-allowlist"}
        blocked = _citation_gate(payload)
        if blocked:
            return {**blocked, "reason": "citation-gate"}
    if name in TERMINAL_TOOLS:
        blocked = _terminal_effect(payload)
        if blocked:
            return {**blocked, "reason": "terminal-effect"}
    return None


def _log_policy(
    tool_name: str,
    result: dict[str, Any],
    args: dict[str, Any] | None = None,
) -> None:
    current = run.load_run()
    blocked = result.get("action") == "block"
    try:
        tokens_in = estimate_tokens(json.dumps(args or {}, ensure_ascii=False))
    except TypeError:
        tokens_in = estimate_tokens(str(args or ""))
    bus.append_audit(
        (current or {}).get("run_id") or "",
        {
            "event": "policy-block",
            "action": result.get("action"),
            "tool": tool_name,
            "message": str(result.get("message") or result.get("args") or "")[:400],
            "tokens_in": tokens_in,
            "tokens_out": estimate_tokens(str(result.get("message") or "")),
            "blocked": blocked,
            "reason": result.get("reason") or "policy-block",
        },
    )


def _block(run_id: str, message: str, **extra: Any) -> dict[str, Any]:
    bus.append_audit(run_id, {"event": "block", "message": message, **extra})
    return {"action": "block", "message": message}


def _delegate_fence(
    args: dict[str, Any],
    current: dict[str, Any] | None,
    governor: str,
) -> dict[str, Any] | None:
    run_id = (current or {}).get("run_id") or ""
    cap = run.worker_cap(current)
    if run.active_worker_count(current) >= cap:
        return _block(
            str(run_id),
            f"Governor: worker cap is {cap}. No new delegate_task.",
            tool="delegate_task",
        )
    if governor == "GREEN":
        return None
    if governor in {"RED", "HARD"}:
        return _block(
            str(run_id),
            f"Governor {governor}: no new delegate_task. Synthesize from the ledger.",
            tool="delegate_task",
        )
    goal = str(
        args.get("goal")
        or args.get("prompt")
        or args.get("task")
        or args.get("instruction")
        or ""
    )
    if run.matches_named_gap(goal, run.named_gaps(current)):
        return None
    return _block(
        str(run_id),
        "Governor AMBER: no new delegate_task batches. Depth on a named gap only.",
        tool="delegate_task",
    )


def _budget_fence(
    tool_name: str,
    args: dict[str, Any],
    governor: str,
    current: dict[str, Any] | None,
) -> dict[str, Any] | None:
    run_id = (current or {}).get("run_id") or ""
    if governor == "GREEN":
        return None
    if governor == "AMBER":
        return None
    if governor == "RED" and tool_name in RED_EGRESS_TOOLS:
        return _block(
            str(run_id),
            "Governor RED: block network tools. Synthesize now from the ledger.",
            tool=tool_name,
        )
    if governor in {"RED", "HARD"} and tool_name in TERMINAL_TOOLS:
        command = str(
            args.get("command") or args.get("cmd") or args.get("code") or args.get("script") or ""
        )
        if _EGRESS.search(command) or not command.strip():
            return _block(
                str(run_id),
                f"Governor {governor}: block terminal egress. Synthesize from the ledger.",
                tool=tool_name,
            )
    if governor == "HARD" and tool_name not in READ_ONLY_WHEN_HARD:
        return _block(
            str(run_id),
            "Governor HARD: only ledger tools and brief-path writes remain.",
            tool=tool_name,
        )
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
    key = re.sub(r"\s+", " ", query)
    if run.record_query_hash(key, time.time(), _QUERY_WINDOW_S):
        return {
            "action": "block",
            "message": f"Near-duplicate search in the last 15 minutes: {key[:80]}",
        }
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


def _path_allowed(raw: str, allowed: frozenset[str] | None = None) -> bool:
    """True when the resolved path is under cwd/<allowlisted-dir>/."""
    names = allowed or BRIEF_DIRS
    try:
        raw_path = Path(raw)
    except Exception:
        return False
    if not str(raw).strip():
        return False
    cwd = Path.cwd().resolve()
    candidate = raw_path.resolve() if raw_path.is_absolute() else (cwd / raw_path).resolve()
    try:
        relative = candidate.relative_to(cwd)
    except ValueError:
        return False
    parts = relative.parts
    return bool(parts) and parts[0] in names


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
    if not _path_allowed(path, CITATION_GATE_DIRS):
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
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", content):
        if _STAT_RE.search(sentence) and not _SID_RE.search(sentence):
            offenders.append(sentence.strip()[:180])
        cited = [f"S{m.group(1)}" for m in _SID_RE.finditer(sentence)]
        if cited:
            unsupported = _unsupported_cited_sentence(sentence, cited)
            if unsupported:
                offenders.append(unsupported)
    if offenders:
        return {
            "action": "block",
            "message": "Citation Gate refused this brief:\n- " + "\n- ".join(offenders[:8]),
        }
    return None


def _unsupported_cited_sentence(sentence: str, cited: list[str]) -> str | None:
    claim = _SID_RE.sub("", sentence)
    claim = re.sub(r"^\s*[-*#>]+\s*", "", claim)
    if " — " in claim:
        claim = claim.split(" — ", 1)[1]
    claim = re.sub(r"\s+", " ", claim).strip(" \t\r\n.")
    if not claim:
        return None
    raw = claim_verify({"claim": claim, "candidate_sources": cited})
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if payload.get("error"):
        return None
    if payload.get("status") == "unsupported":
        return f"unsupported cited claim: {sentence.strip()[:180]}"
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
    if _PKG_INSTALL.search(command):
        return {"action": "block", "message": "Blocked: host package install."}
    if _NET_CALL.search(command):
        return {"action": "block", "message": "Blocked: execute_code network egress."}
    for match in _OPEN_WRITE.finditer(command):
        target = match.group("path")
        if not _path_allowed(target):
            return {
                "action": "block",
                "message": f"Blocked: outbound write outside allowlist ({target}).",
            }
    for match in _PATHLIB_WRITE.finditer(command):
        target = match.group("path")
        if not _path_allowed(target):
            return {
                "action": "block",
                "message": f"Blocked: outbound write outside allowlist ({target}).",
            }
    for match in _REDIRECT.finditer(command):
        target = match.group(1).strip("'\"")
        if target.startswith("/dev/"):
            continue
        if not _path_allowed(target):
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
