"""Quote-span selection and exact-substring verification."""

from __future__ import annotations

import re
from typing import Any

from ..runtime import setting

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-']*")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def select_spans(text: str, question: str = "", limit: int | None = None) -> list[dict[str, Any]]:
    max_spans = int(limit or setting("max_card_spans", 3) or 3)
    max_words = int(setting("span_max_words", 25) or 25)
    body = text or ""
    if not body.strip():
        return []
    query_tokens = {t.lower() for t in _WORD_RE.findall(question) if len(t) > 3}
    sentences = re.split(r"(?<=[.!?])\s+", body)
    scored: list[tuple[int, str]] = []
    cursor = 0
    for sentence in sentences:
        start = body.find(sentence, cursor)
        if start < 0:
            start = cursor
        cursor = start + len(sentence)
        words = _WORD_RE.findall(sentence)
        if not words:
            continue
        overlap = sum(1 for word in words if word.lower() in query_tokens)
        scored.append((overlap, sentence.strip(), start))
    scored.sort(key=lambda item: item[0], reverse=True)
    spans: list[dict[str, Any]] = []
    used = set()
    for _score, sentence, start in scored:
        if sentence in used:
            continue
        words = sentence.split()
        clipped = " ".join(words[:max_words])
        if not clipped:
            continue
        off = body.find(clipped, start if start >= 0 else 0)
        if off < 0:
            off = body.find(clipped)
        if off < 0:
            continue
        spans.append({"q": clipped, "off": off, "len": len(clipped)})
        used.add(sentence)
        if len(spans) >= max_spans:
            break
    if not spans and body.strip():
        words = body.split()
        clipped = " ".join(words[:max_words])
        spans.append({"q": clipped, "off": 0, "len": len(clipped)})
    return spans


def verify_claim(claim: str, corpus_text: str) -> dict[str, Any]:
    text = corpus_text or ""
    needle = (claim or "").strip()
    if not needle:
        return {"exact": False, "off": None, "len": 0, "numeric_match": False, "entity_match": False}
    off = text.find(needle)
    exact = off >= 0
    if not exact:
        # try a long contiguous substring of 8+ words
        words = needle.split()
        for size in range(min(len(words), 12), 7, -1):
            for start in range(0, len(words) - size + 1):
                chunk = " ".join(words[start : start + size])
                pos = text.find(chunk)
                if pos >= 0:
                    off = pos
                    needle = chunk
                    break
            if off is not None and off >= 0 and text.find(needle) >= 0 and len(needle.split()) >= 8:
                break
        exact = off is not None and off >= 0 and needle in text
    claim_nums = set(_NUM_RE.findall(claim or ""))
    span_nums = set(_NUM_RE.findall(text[off : off + len(needle)] if off is not None and off >= 0 else ""))
    numeric = (not claim_nums) or bool(claim_nums & span_nums)
    entities = {t.lower() for t in _WORD_RE.findall(claim or "") if t[:1].isupper() and len(t) > 2}
    blob = (text[off : off + max(len(needle), 200)] if off is not None and off >= 0 else text[:400]).lower()
    entity = (not entities) or any(name.lower() in blob for name in entities)
    return {
        "exact": bool(exact),
        "off": off if exact else None,
        "len": len(needle) if exact else 0,
        "span": needle if exact else "",
        "numeric_match": numeric,
        "entity_match": entity,
    }
