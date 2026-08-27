"""Corpus read/write, URL canonicalization, hashing, locking.

Content-addressed, write-once. Thread-safe. Official plugin-data path.
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from ..runtime import plugin_data_root

_LOCK = threading.RLock()
_TRACKING = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
    }
)
_DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
_ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", re.I)


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


def lock() -> threading.Lock:
    return _LOCK


def canonicalize(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    doi = _DOI_RE.search(raw)
    if raw.lower().startswith("doi:") and doi:
        return f"https://doi.org/{doi.group(1)}"
    arxiv = _ARXIV_RE.search(raw)
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv.group(1)}"
    if "://" not in raw and raw.startswith("www."):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.scheme:
        return raw.rstrip("/")
    host = parsed.hostname or ""
    host = host.lower()
    if host.startswith("m."):
        host = host[2:]
    if host.endswith(".ampproject.org"):
        host = host[: -len(".ampproject.org")]
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in _TRACKING
    ]
    path = parsed.path or ""
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    rebuilt = urlunparse(
        (
            parsed.scheme.lower(),
            host + (f":{parsed.port}" if parsed.port else ""),
            path,
            "",
            urlencode(query, doseq=True),
            "",
        )
    )
    return rebuilt


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    with _LOCK:
        if not txt_path.exists():
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


def prune_corpus(retention_days: int) -> list[str]:
    if retention_days <= 0:
        return []
    cutoff = datetime.now(timezone.utc).timestamp() - retention_days * 86400
    removed: list[str] = []
    with _LOCK:
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
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
