"""Budget Governor accounting from pre/post_api_request."""

from __future__ import annotations

from typing import Any

from ..store import bus, run


def pre_api_request(
    session_id: str = "",
    approx_input_tokens: int = 0,
    **kwargs: Any,
) -> None:
    """Observe prompt size only. Token spend is recorded on post_api_request."""
    del session_id
    try:
        extra = kwargs.get("usage") if isinstance(kwargs.get("usage"), dict) else {}
        tokens = int(approx_input_tokens or extra.get("prompt_tokens") or 0)
        current = run.load_run()
        if current:
            bus.append_audit(
                current.get("run_id") or "",
                {
                    "event": "pre_api_request",
                    "approx_input_tokens": tokens,
                    "counted": False,
                    "governor": current.get("governor"),
                },
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
        tokens = int(payload.get("total_tokens") or 0)
        if not tokens:
            tokens = int(
                payload.get("output_tokens") or payload.get("completion_tokens") or 0
            )
        seconds = 0.0
        for key in ("elapsed_s", "duration_s", "elapsed_seconds"):
            if payload.get(key) is not None:
                seconds = float(payload.get(key) or 0)
                break
            if kwargs.get(key) is not None:
                seconds = float(kwargs.get(key) or 0)
                break
        if tokens or seconds:
            updated = run.add_spend(tokens=tokens, seconds=seconds)
            if updated:
                bus.append_audit(
                    updated.get("run_id") or "",
                    {
                        "event": "post_api_request",
                        "tokens": tokens,
                        "seconds": seconds,
                        "governor": updated.get("governor"),
                    },
                )
    except Exception:
        return
