"""Immutable, point-in-time pulls from systems of record.

Financial data is retroactively mutable: a transaction posted last week can be
recategorized today, and last month's "final" number moves. A report that does
not pin the snapshot it was built from cannot be reproduced or defended.
"""
from __future__ import annotations
import json, os, hashlib, threading, datetime as dt
from pathlib import Path
from ..runtime import data_dir
from . import money

_LOCK = threading.RLock()
SCHEMA = 1


def _index_path() -> Path:
    return data_dir() / "snapshots" / "index.json"


def index() -> dict:
    p = _index_path()
    if not p.exists():
        return {"schema": SCHEMA, "snapshots": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": SCHEMA, "snapshots": []}


def _save_index(d: dict) -> None:
    p = _index_path()
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        os.replace(tmp, p)


def create(entity_id: str, source: str, kind: str, period: str,
           rows: list, meta: dict | None = None) -> dict:
    """rows: normalized dicts. Stored write-once; the id is content-addressed."""
    with _LOCK:
        idx = index()
        sid = f"S{1 + len(idx['snapshots'])}"
        payload = json.dumps(rows, sort_keys=True, default=str)
        sha = hashlib.sha256(payload.encode()).hexdigest()
        f = data_dir() / "snapshots" / f"{sid}.json"
        tmp = f.with_suffix(".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, f)
        cur = money.check_currency(rows) if rows else {"ok": True, "currencies": []}
        total = sum(int(r.get("amount_cents", 0)) for r in rows) if cur["ok"] else None
        rec = {"id": sid, "entity": entity_id, "source": source, "kind": kind,
               "period": period, "rows": len(rows), "sha256": sha,
               "pulled_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "currencies": cur["currencies"], "total_cents": total,
               "meta": meta or {}, "file": f"snapshots/{sid}.json"}
        idx["snapshots"].append(rec)
        _save_index(idx)
        return rec


def get(sid: str) -> dict | None:
    for s in index()["snapshots"]:
        if s["id"] == sid:
            return s
    return None


def rows(sid: str) -> list:
    p = data_dir() / "snapshots" / f"{sid}.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def latest(entity_id: str, source: str, kind: str, period: str | None = None) -> dict | None:
    cand = [s for s in index()["snapshots"]
            if s["entity"] == entity_id and s["source"] == source and s["kind"] == kind
            and (period is None or s["period"] == period)]
    return cand[-1] if cand else None


def is_stale(rec: dict, hours: int) -> bool:
    try:
        t = dt.datetime.fromisoformat(rec["pulled_at"])
    except Exception:
        return True
    age = (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 3600
    return age > hours


def diff(old_id: str, new_id: str, key: str = "id") -> dict:
    """Restatement detection: what moved between two pulls of the same thing."""
    o = {r.get(key): r for r in rows(old_id)}
    n = {r.get(key): r for r in rows(new_id)}
    added = [n[k] for k in n.keys() - o.keys()]
    removed = [o[k] for k in o.keys() - n.keys()]
    changed = []
    for k in o.keys() & n.keys():
        if o[k] != n[k]:
            deltas = {f: [o[k].get(f), n[k].get(f)] for f in set(o[k]) | set(n[k])
                      if o[k].get(f) != n[k].get(f)}
            changed.append({"key": k, "changes": deltas})
    ot = sum(int(r.get("amount_cents", 0)) for r in o.values())
    nt = sum(int(r.get("amount_cents", 0)) for r in n.values())
    return {"old": old_id, "new": new_id,
            "added": len(added), "removed": len(removed), "changed": len(changed),
            "total_old_cents": ot, "total_new_cents": nt, "delta_cents": nt - ot,
            "restated": bool(added or removed or changed),
            "samples": {"added": added[:5], "removed": removed[:5], "changed": changed[:5]}}
