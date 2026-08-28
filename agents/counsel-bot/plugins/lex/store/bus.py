"""Corpus: content-addressed, write-once full text for every authority.

Primary law is huge. Nothing raw is allowed to sit in the context window: the
intake hook writes it here and hands the model a bounded card with a pointer.
"""
from __future__ import annotations
import hashlib, json, os, re, threading
from pathlib import Path
from ..runtime import data_dir

_LOCK = threading.RLock()
_TRACKING = re.compile(r"[?&](utm_[a-z]+|fbclid|gclid|ref|src)=[^&#]*", re.I)


def canonical_url(url: str) -> str:
    if not url:
        return ""
    u = url.strip()
    u = _TRACKING.sub("", u)
    u = re.sub(r"[?&]$", "", u)
    u = re.sub(r"^https?://(www\.|m\.)", "https://", u, flags=re.I)
    u = re.sub(r"/amp/?$", "/", u)
    return u.rstrip("/")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def store(text: str, meta: dict) -> dict:
    """Write once. Returns {sha, path, bytes}. Idempotent by content."""
    sha = digest(text)
    d = data_dir() / "corpus"
    p = d / f"{sha}.txt"
    with _LOCK:
        if not p.exists():
            tmp = d / f".{sha}.tmp"
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, p)
        mp = d / f"{sha}.meta.json"
        base = json.loads(mp.read_text()) if mp.exists() else {}
        base.update(meta or {})
        base["sha"] = sha
        base["bytes"] = len(text)
        tmp = d / f".{sha}.meta.tmp"
        tmp.write_text(json.dumps(base, indent=2), encoding="utf-8")
        os.replace(tmp, mp)
    return {"sha": sha, "path": str(p.relative_to(data_dir())), "bytes": len(text)}


def read(sha: str, offset: int = 0, limit: int = 4000, find: str | None = None) -> dict:
    p = data_dir() / "corpus" / f"{sha}.txt"
    if not p.exists():
        return {"error": f"corpus miss for {sha[:12]} — the text was pruned; re-retrieve the authority"}
    text = p.read_text(encoding="utf-8", errors="replace")
    if find:
        i = text.find(find)
        if i >= 0:
            offset = max(0, i - 200)
    chunk = text[offset:offset + limit]
    return {"sha": sha, "offset": offset, "returned": len(chunk),
            "total": len(text), "text": chunk,
            "more": offset + limit < len(text)}


def contains(sha: str, needle: str) -> dict:
    """Exact-substring provenance. The whole anti-hallucination story rests here."""
    p = data_dir() / "corpus" / f"{sha}.txt"
    if not p.exists():
        return {"exact": False, "reason": "corpus miss"}
    text = p.read_text(encoding="utf-8", errors="replace")
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    hay, ned = norm(text), norm(needle)
    i = hay.find(ned)
    if i >= 0:
        return {"exact": True, "offset": i, "len": len(ned)}
    # case-insensitive second pass, reported as inexact
    j = hay.lower().find(ned.lower())
    return {"exact": False, "case_insensitive": j >= 0, "offset": j if j >= 0 else None}


def prune(days: int) -> int:
    import time
    cutoff = time.time() - days * 86400
    n = 0
    for p in (data_dir() / "corpus").glob("*.txt"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink(); n += 1
        except OSError:
            pass
    return n
