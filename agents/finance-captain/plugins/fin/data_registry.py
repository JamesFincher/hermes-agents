from __future__ import annotations
import json, functools
from pathlib import Path

_D = Path(__file__).parent / "data"


@functools.lru_cache(maxsize=8)
def _load(name: str) -> dict:
    p = _D / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def metrics() -> dict:
    return _load("metrics.json")


def hats() -> dict:
    return _load("hats.json")


def report_types() -> dict:
    return _load("report_types.json")


def coa_map() -> dict:
    return _load("coa_map.json")


def reports_for_hat(hat: str) -> list:
    return sorted([k for k, v in report_types().items() if hat in v.get("hats", [])])
