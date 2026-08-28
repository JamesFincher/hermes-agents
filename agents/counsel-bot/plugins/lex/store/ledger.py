"""Authority ledger v1. One row per retrieved primary or secondary source."""
from __future__ import annotations
import json, os, threading, datetime as dt
from pathlib import Path
from ..runtime import data_dir, setting
from . import bus

_LOCK = threading.RLock()
SCHEMA = 1
BINDING_RANK = {"scotus": 0, "circuit": 1, "district": 2, "state_high": 1,
                "state_app": 2, "state_trial": 3, "agency": 2, "unknown": 4}


def _path() -> Path:
    return data_dir() / "ledger.json"


def load() -> dict:
    p = _path()
    if not p.exists():
        return {"schema": SCHEMA, "updated_at": None, "authorities": []}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": SCHEMA, "updated_at": None, "authorities": []}
    return migrate(d)


def migrate(d: dict) -> dict:
    v = d.get("schema", 0)
    if v == SCHEMA:
        return d
    for a in d.get("authorities", []):
        a.setdefault("tier", "D")
        a.setdefault("as_of", None)
        a.setdefault("treatment", {"checked": False})
    d["schema"] = SCHEMA
    return d


def save(d: dict) -> None:
    d["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    p = _path()
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        os.replace(tmp, p)


def next_id(d: dict) -> str:
    n = 1 + max([int(a["id"][1:]) for a in d.get("authorities", []) if a.get("id", "A0")[1:].isdigit()] or [0])
    return f"A{n}"


def add(entry: dict, text: str | None = None) -> dict:
    """Dedupes on canonical url, then on citation. Returns the stored row."""
    with _LOCK:
        d = load()
        cu = bus.canonical_url(entry.get("url", ""))
        cit = (entry.get("citation") or "").strip().lower()
        for a in d["authorities"]:
            if (cu and a.get("canonical_url") == cu) or (cit and (a.get("citation") or "").lower() == cit):
                a.update({k: v for k, v in entry.items() if v})
                if text:
                    a.update(bus.store(text, {"auth_id": a["id"], "citation": a.get("citation")}))
                save(d)
                return a
        row = {
            "id": next_id(d),
            "kind": entry.get("kind", "secondary"),
            "citation": entry.get("citation"),
            "title": entry.get("title"),
            "url": entry.get("url"),
            "canonical_url": cu or None,
            "jurisdiction": entry.get("jurisdiction"),
            "court": entry.get("court"),
            "court_level": entry.get("court_level", "unknown"),
            "date": entry.get("date"),
            "as_of": entry.get("as_of") or dt.date.today().isoformat(),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(),
            "origin": entry.get("origin", "manual"),
            "tier": entry.get("tier", "D"),
            "verified": bool(entry.get("verified")),
            "treatment": entry.get("treatment", {"checked": False}),
            "spans": entry.get("spans", []),
            "sha": None, "path": None, "bytes": 0,
            "matter_id": entry.get("matter_id"),
        }
        if text:
            row.update(bus.store(text, {"auth_id": row["id"], "citation": row.get("citation")}))
        d["authorities"].append(row)
        save(d)
        return row


def get(auth_id: str) -> dict | None:
    for a in load()["authorities"]:
        if a["id"] == auth_id:
            return a
    return None


def find_citation(cit: str) -> dict | None:
    c = (cit or "").strip().lower().replace(" ", "")
    for a in load()["authorities"]:
        if (a.get("citation") or "").strip().lower().replace(" ", "") == c:
            return a
    return None


def update(auth_id: str, patch: dict) -> dict | None:
    with _LOCK:
        d = load()
        for a in d["authorities"]:
            if a["id"] == auth_id:
                a.update(patch)
                save(d)
                return a
    return None


def search(q: str = "", kind: str = "any", jurisdiction: str = "") -> list:
    ql = (q or "").lower()
    out = []
    for a in load()["authorities"]:
        if kind != "any" and a.get("kind") != kind:
            continue
        if jurisdiction and a.get("jurisdiction") and a["jurisdiction"] != jurisdiction:
            continue
        blob = " ".join(str(a.get(k) or "") for k in ("citation", "title", "court", "jurisdiction")).lower()
        if not ql or ql in blob:
            out.append(a)
    return out


def is_stale(a: dict) -> bool:
    if a.get("kind") not in ("statute", "regulation", "court_rule"):
        return False
    days = int(setting("authority_staleness_days", 30) or 30)
    try:
        as_of = dt.date.fromisoformat((a.get("as_of") or "")[:10])
    except Exception:
        return True
    return (dt.date.today() - as_of).days > days


def card(a: dict, spans: list | None = None) -> dict:
    """The bounded model-facing view. Never includes full text."""
    return {
        "auth": a["id"], "kind": a.get("kind"), "citation": a.get("citation"),
        "title": (a.get("title") or "")[:180], "court": a.get("court"),
        "jurisdiction": a.get("jurisdiction"), "date": a.get("date"),
        "as_of": a.get("as_of"), "verified": a.get("verified"),
        "treatment": a.get("treatment", {}).get("summary", "unchecked"),
        "stale": is_stale(a),
        "spans": (spans if spans is not None else a.get("spans", []))[:3],
        "full": a.get("path"), "bytes": a.get("bytes", 0),
        "read_more": f"authority_read auth_id={a['id']} offset=0 limit=4000",
        "untrusted": True,
    }
