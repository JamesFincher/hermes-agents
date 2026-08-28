"""Hooks the inception plugin registers. Fail open unless marked policy."""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..store import ledger
from . import digest, distill, fence, footer, governor


def register_sections(ctx: Any) -> None:
    digest.register_section(ctx)


def on_session_start(*_args: Any, **_kwargs: Any) -> None:
    try:
        ledger.save_store(ledger.load_store())
        ledger.add_audit("session_start", "factory store ready")
    except Exception:
        return


def pre_llm_call(*args: Any, **kwargs: Any) -> Any:
    return digest.pre_llm_call(*args, **kwargs)


def pre_tool_call(*args: Any, **kwargs: Any) -> Any:
    return fence.pre_tool_call(*args, **kwargs)


def transform_tool_result(*args: Any, **kwargs: Any) -> Any:
    return distill.transform_tool_result(*args, **kwargs)


def transform_llm_output(*args: Any, **kwargs: Any) -> Any:
    return footer.transform_llm_output(*args, **kwargs)


def pre_api_request(*args: Any, **kwargs: Any) -> Any:
    return governor.pre_api_request(*args, **kwargs)


def post_api_request(*args: Any, **kwargs: Any) -> Any:
    return governor.post_api_request(*args, **kwargs)


def _unused_runtime() -> str:
    return runtime.PLUGIN_ID
