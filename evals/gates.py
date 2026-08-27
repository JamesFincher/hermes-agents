"""Deterministic HDR eval gates. No judge. No network."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_SID = re.compile(r"\[S(\d+)\]")
_STAT = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\b(19|20)\d{2}\b|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b)"
)
_SPLIT = re.compile(r"(?<=[.!?])\s+")


def check_run(run_dir: Path) -> list[str]:
    errors: list[str] = []
    brief = (run_dir / "brief.md").read_text(encoding="utf-8")
    ledger = json.loads((run_dir / "ledger.json").read_text(encoding="utf-8"))
    audit = json.loads((run_dir / "audit.json").read_text(encoding="utf-8"))
    sources = {str(src.get("id")): src for src in ledger.get("sources") or [] if isinstance(src, dict)}
    for match in _SID.finditer(brief):
        sid = f"S{match.group(1)}"
        if sid not in sources:
            errors.append(f"unresolvable {sid}")
    for sentence in _SPLIT.split(brief):
        if _STAT.search(sentence) and not _SID.search(sentence):
            errors.append(f"stat without marker: {sentence.strip()[:80]}")
    corpus_dir = run_dir / "corpus"
    corpus_files = {path.name for path in corpus_dir.glob("*.txt")} if corpus_dir.is_dir() else set()
    ledger_corpus = set()
    for src in sources.values():
        corpus = str(src.get("corpus") or "")
        if corpus:
            name = Path(corpus).name
            ledger_corpus.add(name)
            path = run_dir / corpus
            if not path.is_file():
                errors.append(f"ledger corpus missing: {corpus}")
            else:
                text = path.read_text(encoding="utf-8")
                quote = str(src.get("quote") or "")
                if quote and quote not in text and quote.replace("`", "") not in text:
                    errors.append(f"{src.get('id')} quote not in corpus")
    extra = corpus_files - ledger_corpus
    missing = ledger_corpus - corpus_files
    if extra:
        errors.append(f"corpus without ledger: {sorted(extra)}")
    if missing:
        errors.append(f"ledger without corpus: {sorted(missing)}")
    fetches = [str(item) for item in audit.get("fetches") or []]
    if len(fetches) != len(set(fetches)):
        errors.append("duplicate fetches of the same URL")
    tokens = int(audit.get("tokens") or 0)
    ab = int(audit.get("tier_ab_sources") or 0)
    if ab and tokens / ab > 8000:
        errors.append(f"tokens per A/B source {tokens / ab:.0f} > 8000")
    wall = float(audit.get("wall_seconds") or 0)
    budget = float(audit.get("tier_budget_seconds") or 1)
    if wall > budget:
        errors.append(f"wall {wall} exceeds tier budget {budget}")
    errors.extend(_unsupported_claims(brief, run_dir, sources))
    return errors


def _unsupported_claims(
    brief: str,
    run_dir: Path,
    sources: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for sentence in _SPLIT.split(brief):
        markers = [f"S{m.group(1)}" for m in _SID.finditer(sentence)]
        if not markers:
            continue
        claim = _SID.sub("", sentence).strip()
        words = [w for w in re.findall(r"[A-Za-z0-9%]{4,}", claim)]
        supported = False
        for sid in markers:
            src = sources.get(sid) or {}
            corpus = src.get("corpus")
            if not corpus:
                continue
            text = (run_dir / str(corpus)).read_text(encoding="utf-8")
            if any(word.lower() in text.lower() for word in words[:6]):
                supported = True
        if not supported:
            errors.append(f"unsupported cited sentence: {sentence.strip()[:80]}")
    return errors


def all_fixture_runs(root: Path | None = None) -> list[Path]:
    base = root or Path(__file__).resolve().parent / "fixtures"
    return sorted(path for path in base.iterdir() if path.is_dir())
