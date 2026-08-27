"""Quote-span selection and exact-substring verification.

Offsets in this plugin are UTF-8 byte offsets into the corpus file.
select_spans still ranks by query overlap. That is relevance, not verification.
"""

from __future__ import annotations

import re
from typing import Any

from ..runtime import setting

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-']*")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_SID_RE = re.compile(r"\[S(\d+)\]")
_WS_RE = re.compile(r"\s+")
_ENTITY_STOP = frozenset(
    {
        "the",
        "this",
        "that",
        "these",
        "those",
        "there",
        "their",
        "then",
        "when",
        "what",
        "which",
        "where",
        "while",
        "with",
        "from",
        "into",
        "after",
        "before",
        "under",
        "over",
        "however",
        "therefore",
        "thus",
        "also",
        "only",
        "just",
        "even",
        "still",
        "such",
        "both",
        "each",
        "every",
        "some",
        "any",
        "all",
        "most",
        "many",
        "more",
        "less",
        "and",
        "but",
        "for",
        "nor",
        "not",
        "yet",
        "its",
        "his",
        "her",
        "our",
        "your",
        "was",
        "were",
        "are",
        "been",
        "being",
        "has",
        "had",
        "have",
        "does",
        "did",
        "who",
        "why",
        "how",
    }
)


def collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text or "").strip()


def byte_offset(text: str, char_index: int) -> int:
    if char_index <= 0:
        return 0
    return len((text or "")[:char_index].encode("utf-8"))


def byte_length(text: str) -> int:
    return len((text or "").encode("utf-8"))


def cited_claim_text(sentence: str) -> str:
    """Strip [S#] markers and list prefixes. Keep the whole claim."""
    text = _SID_RE.sub("", sentence or "")
    text = re.sub(r"^[\-\*]\s+", "", text)
    text = collapse_ws(text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def split_cited_sentences(text: str) -> list[str]:
    """Split on lines, then sentence ends. Keep [S#] with the sentence it cites."""
    body = re.sub(r"([.!?])(\s*)((?:\[S\d+\]\s*)+)", r" \3\1", text or "")
    out: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        out.extend(
            part.strip() for part in re.split(r"(?<=[.!?])\s+", line) if part.strip()
        )
    return out


def claim_markers(sentence: str) -> list[str]:
    return [f"S{match.group(1)}" for match in _SID_RE.finditer(sentence or "")]


def is_calibration_line(sentence: str) -> bool:
    """True for unmarked notes that are not claims: gaps, paywall, archive."""
    text = cited_claim_text(sentence)
    return text.startswith(("I did not find", "Not found", "archived", "paywall"))


def claim_digits(text: str) -> list[str]:
    return _NUM_RE.findall(text or "")


def claim_entities(text: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for token in _WORD_RE.findall(text or ""):
        if not token[:1].isupper() or len(token) <= 2:
            continue
        key = token.lower()
        if key in _ENTITY_STOP or key in seen:
            continue
        seen.add(key)
        names.append(token)
    return names


def find_exact_span(claim: str, corpus_text: str) -> tuple[int, int, str] | None:
    """Whole-claim match. Whitespace collapse is allowed. No n-gram fallback."""
    text = corpus_text or ""
    needle = collapse_ws(claim)
    if not needle:
        return None
    raw = (claim or "").strip()
    if raw and raw in text:
        char_at = text.find(raw)
        return (byte_offset(text, char_at), byte_length(raw), raw)
    if needle in text:
        char_at = text.find(needle)
        return (byte_offset(text, char_at), byte_length(needle), needle)
    words = needle.split()
    if not words:
        return None
    pattern = re.compile(r"\s+".join(re.escape(word) for word in words))
    match = pattern.search(text)
    if not match:
        return None
    span = match.group(0)
    return (byte_offset(text, match.start()), byte_length(span), span)


def verify_claim(
    claim: str,
    corpus_text: str,
    quote_text: str = "",
) -> dict[str, Any]:
    empty = {
        "exact": False,
        "off": None,
        "len": 0,
        "span": "",
        "numeric_match": False,
        "entity_match": False,
        "missing_digits": claim_digits(claim),
        "missing_entities": [name.lower() for name in claim_entities(claim)],
        "unsupported_parts": [collapse_ws(claim)] if collapse_ws(claim) else [],
    }
    needle = collapse_ws(claim)
    if not needle:
        return empty
    found = find_exact_span(needle, corpus_text)
    if found is None:
        return empty
    off, length, span = found
    check_blob = collapse_ws(quote_text) if quote_text.strip() else span
    missing_digits = [digit for digit in claim_digits(claim) if digit not in check_blob]
    missing_entities = [
        name.lower()
        for name in claim_entities(claim)
        if name.lower() not in check_blob.lower()
    ]
    parts: list[str] = []
    parts.extend(f"missing_digit:{digit}" for digit in missing_digits)
    parts.extend(f"missing_entity:{name}" for name in missing_entities)
    numeric = not missing_digits
    entity = not missing_entities
    return {
        "exact": True,
        "off": off,
        "len": length,
        "span": span,
        "numeric_match": numeric,
        "entity_match": entity,
        "missing_digits": missing_digits,
        "missing_entities": missing_entities,
        "unsupported_parts": parts,
    }


def select_spans(text: str, question: str = "", limit: int | None = None) -> list[dict[str, Any]]:
    max_spans = int(limit or setting("max_card_spans", 3) or 3)
    max_words = int(setting("span_max_words", 25) or 25)
    body = text or ""
    if not body.strip():
        return []
    query_tokens = {t.lower() for t in _WORD_RE.findall(question) if len(t) > 3}
    sentences = re.split(r"(?<=[.!?])\s+", body)
    scored: list[tuple[int, str, int]] = []
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
        off_char = body.find(clipped, start if start >= 0 else 0)
        if off_char < 0:
            off_char = body.find(clipped)
        if off_char < 0:
            continue
        spans.append(
            {
                "q": clipped,
                "off": byte_offset(body, off_char),
                "len": byte_length(clipped),
            }
        )
        used.add(sentence)
        if len(spans) >= max_spans:
            break
    if not spans and body.strip():
        words = body.split()
        clipped = " ".join(words[:max_words])
        spans.append({"q": clipped, "off": 0, "len": byte_length(clipped)})
    return spans
