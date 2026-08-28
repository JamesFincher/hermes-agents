"""Free output. Deterministic factory footer. Zero inference."""

from __future__ import annotations

from typing import Any

from ..store import ledger

MARKER = "\n\n---\nFactory run"


def transform_llm_output(*args: Any, **kwargs: Any) -> Any:
    try:
        text = kwargs.get("text") or kwargs.get("output") or kwargs.get("response")
        if text is None and args:
            text = args[0]
        if not isinstance(text, str):
            return None
        if MARKER in text:
            return None
        data = ledger.load_store()
        probes = data.get("probes") or []
        unv = sum(1 for row in probes if isinstance(row, dict) and row.get("tag") == "UNV")
        footer = (
            f"{MARKER}: probes={len(probes)} unv={unv} "
            f"scaffolds={len(data.get('scaffolds') or [])} "
            f"checks={len(data.get('checks') or [])}. "
            "Next: probe, then scaffold, then check."
        )
        return text + footer
    except Exception:
        return None
