"""Static prompt section + capped volatile digest."""

from __future__ import annotations

from typing import Any

from ..runtime import DIGEST_MAX_CHARS, setting
from ..store import ledger

FACTORY_SECTION = (
    "Factory contract. Isolation is the law. Do not import another profile's "
    "plugin, tools, or skills. Probe official docs before a knob. Tag every "
    "claim [DOC], [INF], or [UNV]. Code never depends on [UNV]. SOUL is "
    "identity only. A skill is a recipe. A tool is a schema plus handler. "
    "A plugin is the host package that registers tools. MCP is a backend. "
    "Call facade names, not raw MCP names. Write HONEST-LIMITS.md. Ship an eval."
)


def register_section(ctx: Any) -> None:
    register = getattr(ctx, "register_system_prompt_section", None)
    if not callable(register):
        return
    try:
        register(
            "inception.factory-contract",
            FACTORY_SECTION,
            position="after_memory",
            max_chars=4000,
        )
    except Exception:
        return


def pre_llm_call(*_args: Any, **_kwargs: Any) -> Any:
    try:
        cap = int(setting("digest_max_chars", DIGEST_MAX_CHARS) or DIGEST_MAX_CHARS)
        cap = max(0, min(cap, DIGEST_MAX_CHARS))
        text = ledger.digest_payload(cap)
        return {"context": text[:cap]}
    except Exception:
        return None
