"""Budget Governor accounting from pre/post_api_request."""

from __future__ import annotations

from typing import Any

from ..store import bus, run


def pre_api_request(
    session_id: str = "",
    approx_input_tokens: int = 0,
    **kwargs: Any,
) -> None:
    del session_id
    try:
        extra = kwargs.get("usage") if isinstance(kwargs.get("usage"), dict) else {}
        tokens = int(approx_input_tokens or extra.get("prompt_tokens") or 0)
        if tokens:
            updated = run.add_spend(tokens=tokens)
            if updated:
                bus.append_audit(
                    updated.get("run_id") or "",
                    {"event": "pre_api_request", "tokens": tokens, "governor": updated.get("governor")},
                )
    except Exception:
        return


def post_api_request(
    session_id: str = "",
    usage: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    del session_id
    try:
        payload = usage if isinstance(usage, dict) else kwargs.get("usage")
        if not isinstance(payload, dict):
            payload = {}
        tokens = int(
            payload.get("total_tokens")
            or payload.get("output_tokens")
            or payload.get("completion_tokens")
            or 0
        )
        if tokens:
            updated = run.add_spend(tokens=tokens)
            if updated:
                bus.append_audit(
                    updated.get("run_id") or "",
                    {"event": "post_api_request", "tokens": tokens, "governor": updated.get("governor")},
                )
    except Exception:
        return
