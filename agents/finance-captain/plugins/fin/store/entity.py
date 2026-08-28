"""Entity + period state: whose books, which period, what is closed."""
from __future__ import annotations
import json, os, threading, datetime as dt
from pathlib import Path
from ..runtime import data_dir

_LOCK = threading.RLock()


def _active_path() -> Path:
    return data_dir() / "active_entity.json"


def active_id() -> str | None:
    p = _active_path()
    if p.exists():
        try:
            return json.loads(p.read_text()).get("entity_id")
        except Exception:
            return None
    return None


def set_active(eid: str) -> None:
    _active_path().write_text(json.dumps({"entity_id": eid}), encoding="utf-8")


def _path(eid: str) -> Path:
    return data_dir() / "entities" / f"{eid}.json"


def load(eid: str | None = None) -> dict | None:
    eid = eid or active_id()
    if not eid:
        return None
    p = _path(eid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(e: dict) -> dict:
    e["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    p = _path(e["entity_id"])
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(e, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    return e


def create(name: str, currency: str, fiscal_year_end: str, basis: str,
           systems: dict, hat: str | None = None) -> dict:
    eid = "E" + dt.datetime.now().strftime("%y%m%d%H%M%S")
    e = {"entity_id": eid, "name": name, "home_currency": currency,
         "fiscal_year_end": fiscal_year_end, "basis": basis,
         "systems": systems or {}, "hat": hat,
         "periods": {}, "open_items": [], "assumptions": [],
         "created": dt.datetime.now(dt.timezone.utc).isoformat()}
    save(e)
    set_active(eid)
    return e


def period(eid: str, p: str) -> dict:
    e = load(eid) or {}
    return e.get("periods", {}).get(p, {"status": "open", "checklist": {}})


def set_period(eid: str, p: str, patch: dict) -> dict:
    with _LOCK:
        e = load(eid)
        cur = e.setdefault("periods", {}).setdefault(p, {"status": "open", "checklist": {}})
        cur.update(patch)
        save(e)
        return cur


def is_closed(eid: str, p: str) -> bool:
    return period(eid, p).get("status") == "closed"


CLOSE_CHECKLIST = [
    "bank_accounts_reconciled",
    "credit_cards_reconciled",
    "ar_aging_reviewed",
    "ap_complete_and_accrued",
    "payroll_recorded",
    "prepaid_and_deferred_amortized",
    "revenue_recognition_reviewed",
    "intercompany_eliminated",
    "uncategorized_cleared",
    "anomaly_scan_reviewed",
    "flux_analysis_explained",
    "balance_sheet_tied_to_support",
]
