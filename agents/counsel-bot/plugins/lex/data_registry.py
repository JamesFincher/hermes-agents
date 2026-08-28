"""Loads the JSON data files: document types, hats, jurisdictions."""
from __future__ import annotations
import json, functools
from pathlib import Path

_D = Path(__file__).parent / "data"


@functools.lru_cache(maxsize=8)
def _load(name: str) -> dict:
    p = _D / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def doc_types() -> dict:
    return _load("doc_types.json")


def hats() -> dict:
    return _load("hats.json")


def jurisdictions() -> dict:
    return _load("jurisdictions.json")


def doc_types_for_hat(hat: str) -> list:
    return sorted([k for k, v in doc_types().items() if hat in v.get("hats", [])])


def hat_notes(hat: str) -> dict:
    return hats().get(hat, {})


def doc_spec(doc_type: str) -> dict | None:
    return doc_types().get(doc_type)
