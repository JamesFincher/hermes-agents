from __future__ import annotations
import json, datetime as dt
from ..runtime import data_dir


def write(stream: str, entry: dict) -> None:
    try:
        p = data_dir() / "audit" / f"{stream}.jsonl"
        entry = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), **entry}
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


def tail(stream: str, n: int = 50) -> list:
    p = data_dir() / "audit" / f"{stream}.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().splitlines()[-n:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out
