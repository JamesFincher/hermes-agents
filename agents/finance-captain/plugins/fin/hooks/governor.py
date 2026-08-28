from __future__ import annotations
from ..store import audit


def post_tool_call(tool_name=None, args=None, result=None, duration_ms=0, **kwargs):
    try:
        audit.write("tools", {"tool": tool_name, "ms": duration_ms,
                              "bytes": len(result or ""),
                              "error": '"error"' in (result or "")[:200]})
    except Exception:
        pass


def pre_api_request(approx_input_tokens=None, model=None, **kwargs):
    try:
        if approx_input_tokens and int(approx_input_tokens) > 150000:
            audit.write("tools", {"warn": "large_context", "tokens": approx_input_tokens})
    except Exception:
        pass


def post_api_request(usage=None, **kwargs):
    try:
        if isinstance(usage, dict):
            audit.write("tools", {"usage": usage})
    except Exception:
        pass
