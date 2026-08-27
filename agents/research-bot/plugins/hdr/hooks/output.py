"""transform_llm_output: deterministic bibliography. Zero inference tokens."""

from __future__ import annotations

import json
import re
from typing import Any

from ..runtime import citation_style
from ..tools.citation import cite_source

_SID_RE = re.compile(r"\[S(\d+)\]")
_STAT_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\b(19|20)\d{2}\b|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b)"
)


def transform_llm_output(text: str, **kwargs: Any) -> str | None:
    del kwargs
    try:
        body = text or ""
        ids = [f"S{m.group(1)}" for m in _SID_RE.finditer(body)]
        if not ids:
            flagged = _flag_uncited(body)
            return flagged if flagged != body else None
        if re.search(r"^##\s+Sources\b", body, re.M):
            return None
        raw = cite_source({"ids": list(dict.fromkeys(ids)), "style": citation_style()})
        payload = json.loads(raw)
        if payload.get("error"):
            return None
        lines = ["", "## Sources"]
        for row in payload.get("citations") or []:
            lines.append(f"[{row.get('id')}] {row.get('text')}")
        extra = _flag_uncited(body)
        return extra + "\n".join(lines)
    except Exception:
        return None


def _flag_uncited(body: str) -> str:
    notes: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", body):
        if _STAT_RE.search(sentence) and not _SID_RE.search(sentence):
            notes.append(sentence.strip()[:160])
    if not notes:
        return body
    banner = (
        "\n\n[HDR] Uncited statistic or date in chat (Citation Gate only fires on brief writes):\n- "
        + "\n- ".join(notes[:5])
    )
    if banner in body:
        return body
    return body + banner
