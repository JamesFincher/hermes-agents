"""Run factory validator rules against one profile path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from ..runtime import dump, error, find_repo_root
from ..store import ledger


def _collector():
    root = find_repo_root()
    if root is None:
        return None, "library root not found (docs/PROFILE-PLAYBOOK.md missing)"
    path = root / "scripts" / "validate_factory.py"
    if not path.is_file():
        return None, "scripts/validate_factory.py missing"
    name = "inception_validate_factory"
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__file__", None) == str(path):
        return existing.collect_agent_errors, None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None, "unable to load validate_factory.py"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.collect_agent_errors, None


def check_profile(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        raw_path = str((args or {}).get("path") or "").strip()
        if not raw_path:
            return error("path is required")
        target = Path(raw_path)
        if not target.is_absolute():
            root = find_repo_root()
            target = (root / raw_path) if root is not None else Path.cwd() / raw_path
        target = target.resolve()
        if not target.is_dir():
            return error(f"not a directory: {target}")
        collector, load_error = _collector()
        if collector is None:
            return error(load_error or "validator unavailable")
        gaps = [str(item) for item in collector(target)]
        row = ledger.add_check({"path": str(target), "gaps": gaps, "ok": not gaps})
        return dump({"ok": not gaps, "path": str(target), "gaps": gaps, "check_id": row.get("id")})
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
