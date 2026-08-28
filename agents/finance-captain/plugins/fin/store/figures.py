"""The figure store — provenance for every number this profile publishes.

A figure is a computed value with its formula, its inputs, its snapshot, and
its period. Reports reference figures by id: `revenue was $1,240,338 [F7]`.
The number fence checks that every number in a report is backed by a figure
whose stored value MATCHES. That catches the two real failure modes: an
invented number, and a stale number copied forward after the data changed.
"""
from __future__ import annotations
import json, os, threading, datetime as dt
from pathlib import Path
from ..runtime import data_dir
from . import money

_LOCK = threading.RLock()


def _path() -> Path:
    return data_dir() / "figures" / "figures.json"


def load() -> dict:
    p = _path()
    if not p.exists():
        return {"schema": 1, "figures": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": 1, "figures": []}


def save(d: dict) -> None:
    p = _path()
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        os.replace(tmp, p)


def record(label: str, value_cents: int | None, formula: str, inputs: dict,
           snapshot_ids: list, period: str, entity: str,
           currency: str = "USD", unit: str = "cents", raw=None) -> dict:
    with _LOCK:
        d = load()
        fid = f"F{1 + len(d['figures'])}"
        formatted = (money.fmt(value_cents, currency) if unit == "cents" and value_cents is not None
                     else str(raw if raw is not None else value_cents))
        rec = {"id": fid, "label": label, "unit": unit, "currency": currency,
               "value_cents": value_cents, "raw": raw, "formatted": formatted,
               "formula": formula, "inputs": inputs,
               "snapshots": snapshot_ids, "period": period, "entity": entity,
               "computed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        d["figures"].append(rec)
        save(d)
        return rec


def get(fid: str) -> dict | None:
    for f in load()["figures"]:
        if f["id"] == fid:
            return f
    return None


def by_period(entity: str, period: str) -> list:
    return [f for f in load()["figures"] if f["entity"] == entity and f["period"] == period]
