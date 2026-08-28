"""Governor. Counts API spend. HARD closes factory writes."""

from __future__ import annotations

from typing import Any

from ..runtime import GOVERNOR_MAX_INPUT_TOKENS, GOVERNOR_MAX_REQUESTS, setting
from ..store import ledger


def _payload(*args: Any, **kwargs: Any) -> dict[str, Any]:
    for candidate in (kwargs.get("payload"), kwargs.get("data"), args[0] if args else None):
        if isinstance(candidate, dict):
            return candidate
    return {}


def pre_api_request(*args: Any, **kwargs: Any) -> Any:
    try:
        payload = _payload(*args, **kwargs)
        tokens = payload.get("approx_input_tokens")
        data = ledger.load_store()
        gov = data.setdefault("governor", {"requests": 0, "input_tokens": 0, "state": "OK"})
        if not isinstance(gov, dict):
            gov = {"requests": 0, "input_tokens": 0, "state": "OK"}
            data["governor"] = gov
        gov["requests"] = int(gov.get("requests") or 0) + 1
        if isinstance(tokens, (int, float)):
            gov["input_tokens"] = int(gov.get("input_tokens") or 0) + int(tokens)
        max_req = int(setting("governor_max_requests", GOVERNOR_MAX_REQUESTS))
        max_tok = int(setting("governor_max_input_tokens", GOVERNOR_MAX_INPUT_TOKENS))
        if gov["requests"] > max_req or int(gov.get("input_tokens") or 0) > max_tok:
            gov["state"] = "HARD"
        ledger.save_store(data)
    except Exception:
        return None
    return None


def post_api_request(*_args: Any, **_kwargs: Any) -> Any:
    return None
