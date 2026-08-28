"""Matter state: jurisdiction, hat, parties, the fact table, the issue plan.

The fact table is the fence. A concrete particular that is not in here cannot
appear in a draft except as a [[FACT:...]] placeholder.
"""
from __future__ import annotations
import json, os, re, threading, datetime as dt
from pathlib import Path
from ..runtime import data_dir

_LOCK = threading.RLock()
SCHEMA = 1


def _active_path() -> Path:
    return data_dir() / "active_matter.json"


def _matter_path(mid: str) -> Path:
    return data_dir() / "matters" / f"{mid}.json"


def active_id() -> str | None:
    p = _active_path()
    if p.exists():
        try:
            return json.loads(p.read_text()).get("matter_id")
        except Exception:
            return None
    return None


def set_active(mid: str) -> None:
    with _LOCK:
        _active_path().write_text(json.dumps({"matter_id": mid}), encoding="utf-8")


def load(mid: str | None = None) -> dict | None:
    mid = mid or active_id()
    if not mid:
        return None
    p = _matter_path(mid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(m: dict) -> dict:
    m["schema"] = SCHEMA
    m["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    p = _matter_path(m["matter_id"])
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(m, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    return m


def create(name: str, jurisdiction: str, forum: str, posture: str,
           parties: list, represented_party: str) -> dict:
    mid = "M" + dt.datetime.now().strftime("%y%m%d%H%M%S")
    m = {"schema": SCHEMA, "matter_id": mid, "name": name,
         "jurisdiction": jurisdiction, "forum": forum, "posture": posture,
         "parties": parties or [], "represented_party": represented_party,
         "hat": None, "facts": {}, "issues": [], "drafts": [],
         "assumptions": [], "open_questions": [],
         "opened": dt.datetime.now(dt.timezone.utc).isoformat(),
         "budget": {"tokens": 0, "fetches": 0, "api_calls": 0}}
    save(m)
    set_active(mid)
    return m


def list_matters() -> list:
    out = []
    for p in (data_dir() / "matters").glob("M*.json"):
        try:
            d = json.loads(p.read_text())
            out.append({k: d.get(k) for k in ("matter_id", "name", "jurisdiction", "hat", "posture")})
        except Exception:
            pass
    return sorted(out, key=lambda x: x["matter_id"], reverse=True)


def add_fact(mid: str, key: str, value: str, source: str) -> dict:
    with _LOCK:
        m = load(mid)
        if not m:
            return {"error": "no active matter"}
        m["facts"][key] = {"value": value, "source": source,
                           "added": dt.datetime.now(dt.timezone.utc).isoformat()}
        save(m)
        return m["facts"][key]


def fact_values(mid: str | None = None) -> set:
    m = load(mid) or {}
    vals = set()
    for f in (m.get("facts") or {}).values():
        v = str(f.get("value", "")).strip()
        if v:
            vals.add(v)
            vals.add(re.sub(r"\s+", " ", v))
    for p in m.get("parties", []) or []:
        if p.get("name"):
            vals.add(p["name"])
    for k in ("name", "forum", "jurisdiction"):
        if m.get(k):
            vals.add(str(m[k]))
    return vals
