"""Inverted index for evidence_search. BM25-ish over titles, spans, claims."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from . import bus

_TOKEN = re.compile(r"[a-z0-9]{3,}")


def index_path():
    return bus.index_dir() / "inverted.json"


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


def _load_unlocked() -> dict[str, Any]:
    path = index_path()
    if not path.is_file():
        return {"docs": {}, "df": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"docs": {}, "df": {}}
    if not isinstance(raw, dict):
        return {"docs": {}, "df": {}}
    raw.setdefault("docs", {})
    raw.setdefault("df", {})
    return raw


def _save_unlocked(data: dict[str, Any]) -> None:
    bus.atomic_write(index_path(), json.dumps(data, ensure_ascii=False) + "\n")


def _claim_texts(source: dict[str, Any], graph: dict[str, Any] | None = None) -> list[str]:
    if graph is None:
        from . import claims

        graph = claims.load_claims()
    texts: list[str] = []
    for claim in source.get("claims") or []:
        key = str(claim)
        node = graph.get(key) if isinstance(graph, dict) else None
        if isinstance(node, dict) and node.get("text"):
            texts.append(str(node["text"]))
        else:
            texts.append(key)
    return texts


def update_source(source: dict[str, Any], claim_graph: dict[str, Any] | None = None) -> None:
    sid = str(source.get("id") or "")
    if not sid:
        return
    parts = [
        str(source.get("title") or ""),
        str(source.get("quote") or ""),
        str(source.get("publisher") or ""),
        " ".join(str(item) for item in (source.get("authors") or [])),
    ]
    for span in source.get("spans") or []:
        if isinstance(span, dict):
            parts.append(str(span.get("q") or ""))
    parts.extend(_claim_texts(source, claim_graph))
    tokens = tokenize(" ".join(parts))
    tf: dict[str, int] = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    with bus.lock():
        data = _load_unlocked()
        docs = data["docs"]
        df = data["df"]
        prior = docs.get(sid) or {}
        if isinstance(prior, dict):
            for token in prior:
                df[token] = max(0, int(df.get(token) or 0) - 1)
                if df[token] == 0:
                    df.pop(token, None)
        docs[sid] = tf
        for token in tf:
            df[token] = int(df.get(token) or 0) + 1
        _save_unlocked(data)


def search(query: str, limit: int = 25) -> list[tuple[str, float]]:
    tokens = tokenize(query)
    if not tokens:
        return []
    with bus.lock():
        data = _load_unlocked()
        docs = data.get("docs") or {}
        df = data.get("df") or {}
        n_docs = max(1, len(docs))
        scores: dict[str, float] = {}
        k1 = 1.2
        b = 0.75
        avg_len = (
            sum(sum(tf.values()) for tf in docs.values() if isinstance(tf, dict)) / n_docs
        )
        avg_len = max(1.0, float(avg_len))
        for sid, tf in docs.items():
            if not isinstance(tf, dict):
                continue
            doc_len = max(1, sum(int(v) for v in tf.values()))
            score = 0.0
            for token in tokens:
                freq = int(tf.get(token) or 0)
                if freq <= 0:
                    continue
                doc_freq = int(df.get(token) or 0)
                idf = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                denom = freq + k1 * (1.0 - b + b * doc_len / avg_len)
                score += idf * (freq * (k1 + 1.0) / denom)
            if score > 0:
                scores[sid] = score
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return ranked[: max(1, limit)]


def rebuild() -> None:
    from . import claims, ledger

    graph = claims.load_claims()
    with bus.lock():
        _save_unlocked({"docs": {}, "df": {}})
    for source in ledger.list_sources():
        update_source(source, claim_graph=graph)
