"""HDR hooks. Official signatures accept **kwargs."""

from .governor import post_api_request, pre_api_request
from .intake import transform_terminal_output, transform_tool_result
from .lifecycle import (
    api_request_error,
    on_session_end,
    on_session_finalize,
    on_session_reset,
    on_session_start,
)
from .output import transform_llm_output
from .policy import post_tool_call, pre_tool_call
from .prompt import METHOD, EFFORT, INTEGRITY, pre_llm_call, register_sections
from .subagents import subagent_start, subagent_stop

__all__ = [
    "METHOD",
    "EFFORT",
    "INTEGRITY",
    "register_sections",
    "on_session_start",
    "on_session_end",
    "on_session_finalize",
    "on_session_reset",
    "api_request_error",
    "pre_llm_call",
    "pre_tool_call",
    "post_tool_call",
    "transform_tool_result",
    "transform_terminal_output",
    "pre_api_request",
    "post_api_request",
    "subagent_start",
    "subagent_stop",
    "transform_llm_output",
]
