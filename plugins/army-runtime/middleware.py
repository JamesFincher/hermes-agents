"""Optional tool_request middleware. Return None for non-matching calls.

Official shape (kwargs + return args/source/reason):
https://github.com/nousresearch/hermes-agent/blob/main/docs/middleware/README.md
"""

from __future__ import annotations

from typing import Any

from . import runtime


def tool_request_defaults(**kwargs: Any) -> dict[str, Any] | None:
    """Fill citation_style on source_ledger_cite when the model omitted it."""
    if kwargs.get("tool_name") != "source_ledger_cite":
        return None
    raw_args = kwargs.get("args")
    if not isinstance(raw_args, dict):
        return None
    if raw_args.get("style"):
        return None
    args = dict(raw_args)
    args["style"] = runtime.citation_style()
    return {
        "args": args,
        "source": "army-runtime",
        "reason": "defaulted citation_style from plugins.entries.army-runtime.settings",
    }
