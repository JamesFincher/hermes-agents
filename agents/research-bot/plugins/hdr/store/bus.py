"""Corpus read/write, URL canonicalization, hashing, locking.

Content-addressed, write-once. Thread-safe and process-safe.
Official plugin-data path.
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ..runtime import plugin_data_root
from .urls import canonicalize

_LOCK = threading.RLock()
_LOCK_DEPTH = 0
_LOCK_FD: int | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def corpus_dir() -> Path:
    path = plugin_data_root() / "corpus"
    path.mkdir(parents=True, exist_ok=True)
    return path


def audit_dir() -> Path:
    path = plugin_data_root() / "audit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def index_dir() -> Path:
    path = plugin_data_root() / "index"
    path.mkdir(parents=True, exist_ok=True)
    return path


def lock_path() -> Path:
    return plugin_data_root() / "ledger.json.lock"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="hdr-", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


@contextmanager
def lock() -> Iterator[None]:
    """Reentrant thread lock plus an exclusive file lock for child processes."""
    global _LOCK_DEPTH, _LOCK_FD
    with _LOCK:
        if _LOCK_DEPTH == 0:
            path = lock_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            _LOCK_FD = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
            fcntl.flock(_LOCK_FD, fcntl.LOCK_EX)
        _LOCK_DEPTH += 1
        try:
            yield
        finally:
            _LOCK_DEPTH -= 1
            if _LOCK_DEPTH == 0 and _LOCK_FD is not None:
                try:
                    fcntl.flock(_LOCK_FD, fcntl.LOCK_UN)
                finally:
                    os.close(_LOCK_FD)
                    _LOCK_FD = None


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_key(value: Any) -> str:
    return str(value or "").replace("sha256:", "").strip().lower()


def wayback_latest_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    return "https://web.archive.org/web/" + raw


def write_corpus(text: str, meta: dict[str, Any]) -> dict[str, Any]:
    body = text if isinstance(text, str) else str(text)
    digest = content_hash(body)
    txt_path = corpus_dir() / f"{digest}.txt"
    meta_path = corpus_dir() / f"{digest}.meta.json"
    record = {
        "sha256": digest,
        "bytes": len(body.encode("utf-8")),
        "chars": len(body),
        "written_at": _now_iso(),
        **meta,
    }
    with lock():
        existed = txt_path.exists()
        if not existed:
            atomic_write(txt_path, body)
        if not meta_path.exists():
            atomic_write(meta_path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return {
        "ok": True,
        "sha256": digest,
        "path": f"corpus/{digest}.txt",
        "abs": str(txt_path),
        "bytes": record["bytes"],
        "chars": record["chars"],
        "existed": existed,
    }


def read_corpus(sha256: str, offset: int = 0, limit: int = 4000) -> dict[str, Any]:
    digest = sha256.replace("sha256:", "").strip()
    path = corpus_dir() / f"{digest}.txt"
    if not path.is_file():
        return {"error": f"corpus file missing: {digest}"}
    text = path.read_text(encoding="utf-8")
    start = max(0, int(offset))
    end = start + max(0, int(limit))
    return {
        "ok": True,
        "sha256": digest,
        "offset": start,
        "limit": limit,
        "total": len(text),
        "text": text[start:end],
    }


def corpus_exists_for_url(canonical: str) -> dict[str, Any] | None:
    from . import ledger

    data = ledger.load_ledger()
    for source in data.get("sources", []):
        if not isinstance(source, dict):
            continue
        if source.get("canonical_url") == canonical and source.get("corpus"):
            return source
    return None


def source_for_hash(digest: str) -> dict[str, Any] | None:
    from . import ledger

    needle = hash_key(digest)
    if not needle:
        return None
    data = ledger.load_ledger()
    for source in data.get("sources", []):
        if not isinstance(source, dict):
            continue
        if hash_key(source.get("content_hash")) == needle:
            return source
        corpus = str(source.get("corpus") or "")
        if needle and needle in corpus:
            return source
    return None


def prune_corpus(retention_days: int) -> list[str]:
    if retention_days <= 0:
        return []
    cutoff = datetime.now(timezone.utc).timestamp() - retention_days * 86400
    removed: list[str] = []
    with lock():
        for path in corpus_dir().glob("*.txt"):
            try:
                if path.stat().st_mtime < cutoff:
                    digest = path.stem
                    meta = path.with_name(path.stem + ".meta.json")
                    path.unlink(missing_ok=True)
                    meta.unlink(missing_ok=True)
                    removed.append(digest)
            except Exception:
                continue
    return removed


def append_audit(run_id: str, event: dict[str, Any]) -> None:
    if not run_id:
        return
    path = audit_dir() / f"{run_id}.jsonl"
    line = json.dumps({"at": _now_iso(), **event}, ensure_ascii=False) + "\n"
    with lock():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


__all__ = [
    "append_audit",
    "atomic_write",
    "audit_dir",
    "canonicalize",
    "content_hash",
    "corpus_dir",
    "corpus_exists_for_url",
    "hash_key",
    "index_dir",
    "lock",
    "lock_path",
    "prune_corpus",
    "read_corpus",
    "source_for_hash",
    "wayback_latest_url",
    "write_corpus",
]
