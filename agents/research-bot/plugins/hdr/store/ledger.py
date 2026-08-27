"""Ledger v2 CRUD, v1 migration, URL dedupe. Thread-safe."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..runtime import plugin_data_root
from . import bus

LEDGER_VERSION = 2
KNOWN_KINDS = frozenset({"primary", "secondary", "tertiary", "dataset", "filing", "spec"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ledger_path() -> Path:
    return plugin_data_root() / "ledger.json"


def empty_ledger() -> dict[str, Any]:
    return {"version": LEDGER_VERSION, "updated_at": _now_iso(), "run_ids": [], "sources": []}


def _next_sid(sources: list[Any]) -> str:
    highest = 0
    for source in sources:
        if not isinstance(source, dict):
            continue
        raw = str(source.get("id") or "")
        if raw.startswith("S") and raw[1:].isdigit():
            highest = max(highest, int(raw[1:]))
        elif isinstance(source.get("id"), int):
            highest = max(highest, int(source["id"]))
    return f"S{highest + 1}"


def _map_kind(raw: Any) -> str:
    kind = str(raw or "").strip().lower()
    if kind in KNOWN_KINDS:
        return kind
    return "secondary"


def _corpus_file_exists(corpus: Any) -> bool:
    raw = str(corpus or "").strip()
    if not raw:
        return False
    name = Path(raw).name
    if not name.endswith(".txt"):
        name = f"{bus.hash_key(raw)}.txt"
    return (bus.corpus_dir() / name).is_file()


def migrate_v1(data: dict[str, Any]) -> dict[str, Any]:
    sources = data.get("sources")
    if not isinstance(sources, list):
        sources = []
    migrated: list[dict[str, Any]] = []
    for index, raw in enumerate(sources, start=1):
        if not isinstance(raw, dict):
            continue
        sid = raw.get("id")
        if isinstance(sid, int):
            sid = f"S{sid}"
        elif not isinstance(sid, str) or not sid.startswith("S"):
            sid = f"S{index}"
        url = str(raw.get("url") or "")
        corpus = raw.get("corpus")
        real_file = _corpus_file_exists(corpus)
        migrated.append(
            {
                "id": sid,
                "run_id": raw.get("run_id") or "",
                "url": url,
                "canonical_url": raw.get("canonical_url") or bus.canonicalize(url),
                "archived_url": raw.get("archived_url"),
                "title": raw.get("title") or "",
                "authors": raw.get("authors") if isinstance(raw.get("authors"), list) else [],
                "publisher": raw.get("publisher") or "",
                "container": raw.get("container") or "",
                "published": raw.get("published"),
                "retrieved": raw.get("retrieved") or _now_iso(),
                "doi": raw.get("doi"),
                "arxiv": raw.get("arxiv"),
                "kind": _map_kind(raw.get("kind")),
                "tier": "D",
                "tier_reason": raw.get("tier_reason") or "migrated-v1",
                "corpus": corpus if real_file else None,
                "bytes": raw.get("bytes") or 0,
                "content_hash": raw.get("content_hash"),
                "spans": raw.get("spans") if isinstance(raw.get("spans"), list) else [],
                "claims": raw.get("claims") if isinstance(raw.get("claims"), list) else [],
                "origin": raw.get("origin") or "manual",
                "fetch_status": raw.get("fetch_status") or "ok",
                "duplicate_of": raw.get("duplicate_of"),
                "needs_backfill": False if real_file else True,
                "quote": raw.get("quote") or "",
            }
        )
    return {
        "version": LEDGER_VERSION,
        "updated_at": _now_iso(),
        "run_ids": list(data.get("run_ids") or []),
        "sources": migrated,
    }


def _load_unlocked() -> dict[str, Any]:
    path = ledger_path()
    if not path.is_file():
        return empty_ledger()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return empty_ledger()
    if not isinstance(raw, dict):
        return empty_ledger()
    version = raw.get("version", 1)
    if version != LEDGER_VERSION:
        raw = migrate_v1(raw)
        bus.atomic_write(path, json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    if not isinstance(raw.get("sources"), list):
        raw["sources"] = []
    if not isinstance(raw.get("run_ids"), list):
        raw["run_ids"] = []
    return raw


def load_ledger() -> dict[str, Any]:
    with bus.lock():
        return _load_unlocked()


def save_ledger(data: dict[str, Any]) -> None:
    data["version"] = LEDGER_VERSION
    data["updated_at"] = _now_iso()
    bus.atomic_write(ledger_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def init_ledger() -> dict[str, Any]:
    with bus.lock():
        data = _load_unlocked()
        if not ledger_path().exists():
            save_ledger(data)
        return data


def _merge_existing(existing: dict[str, Any], entry: dict[str, Any]) -> None:
    for key in (
        "title",
        "quote",
        "publisher",
        "published",
        "doi",
        "arxiv",
        "corpus",
        "content_hash",
        "bytes",
        "spans",
        "archived_url",
        "authors",
        "kind",
        "tier",
        "tier_reason",
        "fetch_status",
        "origin",
        "run_id",
    ):
        value = entry.get(key)
        if value and not existing.get(key):
            existing[key] = value
    if entry.get("needs_backfill") is False:
        existing["needs_backfill"] = False


def add_source(entry: dict[str, Any]) -> dict[str, Any]:
    url = str(entry.get("url") or "").strip()
    if not url:
        return {"error": "url is required"}
    canonical = str(entry.get("canonical_url") or bus.canonicalize(url))
    incoming_hash = bus.hash_key(entry.get("content_hash"))
    with bus.lock():
        data = _load_unlocked()
        sources = data["sources"]
        for existing in sources:
            if not isinstance(existing, dict):
                continue
            if existing.get("canonical_url") == canonical or existing.get("url") == url:
                _merge_existing(existing, entry)
                save_ledger(data)
                from . import index as inverted

                inverted.update_source(existing)
                return {"ok": True, "updated": True, "source": existing}
        if incoming_hash:
            for existing in sources:
                if not isinstance(existing, dict):
                    continue
                if bus.hash_key(existing.get("content_hash")) != incoming_hash:
                    continue
                sid = _next_sid(sources)
                record = _new_record(sid, url, canonical, entry)
                record["duplicate_of"] = existing.get("id")
                record["corpus"] = entry.get("corpus") or existing.get("corpus")
                record["content_hash"] = entry.get("content_hash") or existing.get("content_hash")
                record["bytes"] = entry.get("bytes") or existing.get("bytes") or 0
                record["spans"] = entry.get("spans") or existing.get("spans") or []
                sources.append(record)
                _note_run(data, record.get("run_id") or "")
                save_ledger(data)
                from . import index as inverted

                inverted.update_source(record)
                return {"ok": True, "updated": False, "source": record}
        sid = _next_sid(sources)
        record = _new_record(sid, url, canonical, entry)
        sources.append(record)
        _note_run(data, record.get("run_id") or "")
        save_ledger(data)
        from . import index as inverted

        inverted.update_source(record)
        return {"ok": True, "updated": False, "source": record}


def _note_run(data: dict[str, Any], run_id: str) -> None:
    if run_id and run_id not in data["run_ids"]:
        data["run_ids"].append(run_id)


def _new_record(sid: str, url: str, canonical: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": sid,
        "run_id": entry.get("run_id") or "",
        "url": url,
        "canonical_url": canonical,
        "archived_url": entry.get("archived_url"),
        "title": entry.get("title") or "",
        "authors": entry.get("authors") if isinstance(entry.get("authors"), list) else [],
        "publisher": entry.get("publisher") or "",
        "published": entry.get("published"),
        "retrieved": entry.get("retrieved") or _now_iso(),
        "doi": entry.get("doi"),
        "arxiv": entry.get("arxiv"),
        "kind": entry.get("kind") or "secondary",
        "tier": entry.get("tier") or "C",
        "tier_reason": entry.get("tier_reason") or "",
        "corpus": entry.get("corpus"),
        "bytes": entry.get("bytes") or 0,
        "content_hash": entry.get("content_hash"),
        "spans": entry.get("spans") if isinstance(entry.get("spans"), list) else [],
        "claims": entry.get("claims") if isinstance(entry.get("claims"), list) else [],
        "origin": entry.get("origin") or "manual",
        "fetch_status": entry.get("fetch_status") or "ok",
        "duplicate_of": entry.get("duplicate_of"),
        "needs_backfill": bool(entry.get("needs_backfill", False)),
        "quote": entry.get("quote") or "",
    }


def get_source(src_id: str) -> dict[str, Any] | None:
    data = load_ledger()
    for source in data.get("sources", []):
        if isinstance(source, dict) and source.get("id") == src_id:
            return source
    return None


def list_sources(query: str = "", run_id: str = "") -> list[dict[str, Any]]:
    data = load_ledger()
    sources = [s for s in data.get("sources", []) if isinstance(s, dict)]
    if run_id:
        sources = [s for s in sources if s.get("run_id") == run_id]
    needle = query.strip().lower()
    if needle:
        sources = [
            source
            for source in sources
            if needle
            in " ".join(
                str(source.get(key, ""))
                for key in ("id", "url", "canonical_url", "title", "quote", "kind", "publisher")
            ).lower()
        ]
    return sources


def mark_corpus_gone(sha256: str, archived_url: str | None = None) -> None:
    digest = sha256.replace("sha256:", "")
    with bus.lock():
        data = _load_unlocked()
        for source in data.get("sources", []):
            if not isinstance(source, dict):
                continue
            corpus = str(source.get("corpus") or "")
            hashed = bus.hash_key(source.get("content_hash"))
            if digest in corpus or hashed == bus.hash_key(digest):
                source["corpus"] = None
                if archived_url:
                    source["archived_url"] = archived_url
        save_ledger(data)


def link_claim(src_id: str, cid: str) -> None:
    if not src_id or not cid:
        return
    with bus.lock():
        data = _load_unlocked()
        for source in data.get("sources", []):
            if not isinstance(source, dict) or source.get("id") != src_id:
                continue
            linked = source.setdefault("claims", [])
            if isinstance(linked, list) and cid not in linked:
                linked.append(cid)
        save_ledger(data)
