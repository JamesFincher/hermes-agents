"""Budget Governor accounting from pre/post_api_request."""

from __future__ import annotations

from typing import Any

from ..store import bus, run

_INPUT_KEYS = ("input_tokens", "prompt_tokens")
_OUTPUT_KEYS = ("output_tokens", "completion_tokens")


def usage_mapping(usage: Any) -> dict[str, Any]:
    """Accept a dict or a namespace such as CanonicalUsage."""
    if isinstance(usage, dict):
        return usage
    if usage is None:
        return {}
    payload: dict[str, Any] = {}
    for key in (
        "input_tokens",
        "output_tokens",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "elapsed_s",
        "duration_s",
        "elapsed_seconds",
    ):
        if hasattr(usage, key):
            try:
                payload[key] = getattr(usage, key)
            except Exception:
                continue
    return payload


def tokens_from_usage(usage: Any, *, side: str) -> int:
    payload = usage_mapping(usage)
    keys = _INPUT_KEYS if side == "input" else _OUTPUT_KEYS
    for key in keys:
        raw = payload.get(key)
        if raw is None:
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value:
            return value
    return 0


def total_tokens(usage: Any) -> int:
    payload = usage_mapping(usage)
    raw = payload.get("total_tokens")
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _seconds_from(payload: dict[str, Any], kwargs: dict[str, Any]) -> float:
    for key in ("elapsed_s", "duration_s", "elapsed_seconds"):
        if payload.get(key) is not None:
            try:
                return float(payload.get(key) or 0)
            except (TypeError, ValueError):
                return 0.0
        if kwargs.get(key) is not None:
            try:
                return float(kwargs.get(key) or 0)
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def pre_api_request(
    session_id: str = "",
    approx_input_tokens: int = 0,
    api_request_id: str = "",
    usage: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    """Observe prompt size only. Token spend is recorded on post_api_request."""
    del session_id, api_request_id
    try:
        extra = usage if usage is not None else kwargs.get("usage")
        tokens = tokens_from_usage(extra, side="input") or int(approx_input_tokens or 0)
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
    api_request_id: str = "",
    **kwargs: Any,
) -> None:
    del session_id
    try:
        payload = usage if usage is not None else kwargs.get("usage")
        mapped = usage_mapping(payload)
        request_id = str(api_request_id or kwargs.get("api_request_id") or "")
        seconds = _seconds_from(mapped, kwargs)
        inp = tokens_from_usage(payload, side="input")
        output = tokens_from_usage(payload, side="output")
        counted = False
        if inp:
            run.add_spend(
                tokens=inp,
                seconds=0.0 if output else seconds,
                api_request_id=request_id,
                token_side="input",
            )
            counted = True
        if output:
            run.add_spend(
                tokens=output,
                seconds=seconds,
                api_request_id=request_id,
                token_side="output",
            )
            return
        if counted:
            return
        total = total_tokens(payload)
        if not total and not seconds:
            return
        run.add_spend(
            tokens=total,
            seconds=seconds,
            api_request_id=request_id,
            token_side="total",
        )
    except Exception:
        return
