"""Budget accounting and the audit trail. Observers only — never blocks here."""
from __future__ import annotations
import json, logging
from ..store import matter as M
from ..runtime import data_dir

log = logging.getLogger("lex.governor")


def _bump(field: str, n: int = 1) -> None:
    try:
        m = M.load()
        if not m:
            return
        m.setdefault("budget", {}).setdefault(field, 0)
        m["budget"][field] += n
        M.save(m)
    except Exception:
        pass


def post_tool_call(tool_name=None, args=None, result=None, duration_ms=0, **kwargs):
    try:
        if tool_name in ("web_extract", "web_search", "browser_navigate"):
            _bump("fetches")
        with (data_dir() / "audit" / "tools.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"tool": tool_name, "ms": duration_ms,
                                "bytes": len(result or ""),
                                "error": '"error"' in (result or "")[:200]}, default=str) + "\n")
    except Exception:
        pass


def pre_api_request(approx_input_tokens=None, model=None, **kwargs):
    try:
        if approx_input_tokens:
            _bump("tokens", int(approx_input_tokens))
        _bump("api_calls")
    except Exception:
        pass


def post_api_request(usage=None, model=None, **kwargs):
    try:
        if isinstance(usage, dict):
            out = usage.get("completion_tokens") or usage.get("output_tokens") or 0
            if out:
                _bump("tokens", int(out))
    except Exception:
        pass
