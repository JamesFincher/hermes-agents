"""Writes to systems of record: propose, approve, apply, once.

Anything that changes a book, moves money, or leaves the building is a
mutation. Mutations are never taken directly by the model. They are proposed
with a dry-run diff, approved explicitly by a human for that exact proposal,
and applied once under an idempotency key that survives a retry.
"""
from __future__ import annotations
import json, os, hashlib, threading, datetime as dt
from pathlib import Path
from ..runtime import data_dir
from . import money

_LOCK = threading.RLock()

# Effect classes, most dangerous first.
CLASS = {
    "money_movement": ["pay_bill", "send_payment", "transfer", "refund", "payroll_run"],
    "external_send": ["send_invoice", "email_customer", "post_message", "share_report"],
    "book_write": ["create_journal_entry", "categorize_transaction", "create_invoice",
                   "create_bill", "reconcile_account", "close_period", "void"],
    "read_only": [],
}


def classify(action: str) -> str:
    for k, v in CLASS.items():
        if action in v:
            return k
    return "book_write"   # unknown writes get the stricter treatment, not the looser


def _path() -> Path:
    return data_dir() / "mutations.json"


def load() -> dict:
    p = _path()
    if not p.exists():
        return {"schema": 1, "proposals": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": 1, "proposals": []}


def save(d: dict) -> None:
    p = _path()
    tmp = p.with_suffix(".tmp")
    with _LOCK:
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        os.replace(tmp, p)


def idempotency_key(system: str, action: str, payload: dict) -> str:
    blob = json.dumps({"s": system, "a": action, "p": payload}, sort_keys=True, default=str)
    return "idem_" + hashlib.sha256(blob.encode()).hexdigest()[:24]


def propose(system: str, action: str, payload: dict, entity: str,
            amount_cents: int | None, rationale: str, dry_run_result: dict | None) -> dict:
    with _LOCK:
        d = load()
        key = idempotency_key(system, action, payload)
        for p in d["proposals"]:
            if p["idempotency_key"] == key and p["status"] in ("proposed", "applied"):
                return {**p, "note": "identical proposal already exists — not duplicated"}
        pid = f"P{1 + len(d['proposals'])}"
        rec = {"id": pid, "system": system, "action": action, "class": classify(action),
               "entity": entity, "payload": payload,
               "amount_cents": amount_cents,
               "amount": money.fmt(amount_cents) if amount_cents is not None else None,
               "rationale": rationale, "dry_run": dry_run_result,
               "idempotency_key": key, "status": "proposed",
               "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "approved_by": None, "approved_at": None, "applied_at": None,
               "result": None}
        d["proposals"].append(rec)
        save(d)
        return rec


def approve(pid: str, approver: str) -> dict | None:
    with _LOCK:
        d = load()
        for p in d["proposals"]:
            if p["id"] == pid:
                if p["status"] != "proposed":
                    return {**p, "error": f"cannot approve a proposal in status {p['status']}"}
                p["status"] = "approved"
                p["approved_by"] = approver
                p["approved_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                save(d)
                return p
    return None


def mark_applied(pid: str, result: dict) -> dict | None:
    with _LOCK:
        d = load()
        for p in d["proposals"]:
            if p["id"] == pid:
                p["status"] = "applied"
                p["applied_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                p["result"] = result
                save(d)
                return p
    return None


def get(pid: str) -> dict | None:
    for p in load()["proposals"]:
        if p["id"] == pid:
            return p
    return None
