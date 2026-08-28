"""Write a validator-passing agents/<name>/ skeleton. No foreign internals."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..runtime import (
    FORBIDDEN_CROSS_IDS,
    OUROBOROS_PLUGIN_NAMES,
    RESERVED_PROFILE_NAMES,
    dump,
    error,
    find_repo_root,
)
from ..store import ledger
from ..store import plan as plan_store

_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,47}$")


def _validate_name(name: str) -> str | None:
    if not _NAME_RE.match(name):
        return "name must be lowercase letters, digits, and hyphens"
    if name in RESERVED_PROFILE_NAMES:
        return f"reserved profile name: {name}"
    if name in OUROBOROS_PLUGIN_NAMES:
        return f"ouroboros plugin-name collision: {name}"
    if name in FORBIDDEN_CROSS_IDS or name == "inception":
        return f"forbidden profile name: {name}"
    return None


def _templates(name: str, job: str, author: str) -> dict[str, str]:
    peer = f"hermes.{name}"
    return {
        "distribution.yaml": (
            f'name: {name}\n'
            f'version: 0.1.0\n'
            f'description: "{job}"\n'
            f'hermes_requires: ">=0.13.0"\n'
            f'author: "{author}"\n'
            f'license: "Apache-2.0"\n'
            f"distribution_owned:\n"
            f"  - SOUL.md\n"
            f"  - config.yaml\n"
            f"  - skills\n"
            f"  - distribution.yaml\n"
            f"  - profile.yaml\n"
            f"  - honcho.json.example\n"
            f"  - README.md\n"
            f"  - HONEST-LIMITS.md\n"
            f"  - .gitignore\n"
            f"env_requires: []\n"
        ),
        "profile.yaml": (
            f'description: "{job}"\n'
            f"description_auto: false\n"
        ),
        "SOUL.md": (
            f"# Soul\n\n"
            f"You do one job. {job}\n\n"
            f"## Identity\n\n"
            f"You are a specialist. You finish the job and stop.\n\n"
            f"## Style\n\n"
            f"Lead with the answer. One idea per sentence. Common words.\n\n"
            f"## Avoid\n\n"
            f"Invented platform knobs. Shared runtimes. Product work outside the job.\n\n"
            f"## Defaults\n\n"
            f"If the request is ambiguous, ask one question, then proceed.\n"
        ),
        "config.yaml": (
            f"# Skill-only skeleton. Add a plugin only if the canvas requires tools.\n"
            f"# Official: https://hermes-agent.nousresearch.com/docs/user-guide/configuration\n"
            f"memory:\n"
            f"  provider: honcho\n"
            f"  memory_enabled: true\n"
            f"  user_profile_enabled: true\n"
            f"  memory_char_limit: 1200\n"
            f"  user_char_limit: 800\n"
            f"  write_approval: false\n"
            f"skills:\n"
            f"  inline_shell: false\n"
            f"  write_approval: false\n"
            f"  guard_agent_created: true\n"
            f"compression:\n"
            f"  enabled: true\n"
            f"  threshold: 0.55\n"
            f"  tail_mode: lean\n"
            f"  in_place: true\n"
            f"  proactive_prune_tokens: 32000\n"
            f"  proactive_prune_min_result_chars: 4000\n"
            f"  proactive_prune_min_reclaim_tokens: 4096\n"
            f"agent:\n"
            f"  verify_on_stop: false\n"
        ),
        "README.md": (
            f"# {name}\n\n"
            f"{job}\n\n"
            f"This profile is one shelf item in the Hermes Agent Profile Library. "
            f"It does not share a plugin, a toolset, or skills with another profile.\n\n"
            f"Install:\n\n"
            f"```bash\n"
            f"hermes profile install ./agents/{name} --alias\n"
            f"```\n\n"
            f"Limits: [`HONEST-LIMITS.md`](HONEST-LIMITS.md).\n"
        ),
        "HONEST-LIMITS.md": (
            f"# Honest limits — {name}\n\n"
            f"This is a playbook skeleton. It is not a finished specialist.\n\n"
            f"- No custom plugin ships yet. Add one only if the canvas requires tools.\n"
            f"- Eval is not frozen. A profile that ships without eval does not ship.\n"
            f"- Live Hermes CLI install is unproven until an operator runs it.\n"
        ),
        "INTEGRATION.md": (
            f"# {name} instance\n\n"
            f"**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md)\n\n"
            f"Skill-only skeleton. SOUL is identity. Skills live in `skills/`. "
            f"Memory is `memory.provider: honcho`. Unique `aiPeer`: `{peer}`. "
            f"`pinUserPeer: true` is official and gateway-only.\n\n"
            f"This profile starts empty of research-bot and inception internals. "
            f"It must not enable `hdr`.\n"
        ),
        ".gitignore": (
            "auth.json\n.env\nstate.db\nmemories/\nsessions/\nlogs/\n"
            "plugin-data/\nhoncho.json\ncache/\n"
        ),
        "honcho.json.example": (
            "{\n"
            '  "workspace": "hermes",\n'
            '  "hosts": {\n'
            f'    "{peer}": {{\n'
            f'      "enabled": true,\n'
            f'      "aiPeer": "{peer}",\n'
            f'      "workspace": "hermes",\n'
            f'      "recallMode": "hybrid",\n'
            f'      "writeFrequency": "async",\n'
            f'      "sessionStrategy": "per-directory",\n'
            f'      "pinUserPeer": true\n'
            f"    }}\n"
            f"  }}\n"
            f"}}\n"
        ),
        f"skills/do-job/SKILL.md": (
            f"---\n"
            f"name: do-job\n"
            f"description: Do the profile job. {job}\n"
            f"version: 0.1.0\n"
            f"metadata:\n"
            f"  hermes:\n"
            f"    tags: [starter]\n"
            f"---\n\n"
            f"# Do the job\n\n"
            f"## When to Use\n\n"
            f"Use this when the user asks for the profile job.\n\n"
            f"## Quick Reference\n\n"
            f"Read the canvas. Follow the playbook. Do not invent knobs.\n\n"
            f"## Procedure\n\n"
            f"1. Restate the job in one sentence.\n"
            f"2. Use existing Hermes tools only. Do not call raw `mcp_*` tools.\n"
            f"3. Write the result in the repo the user named.\n\n"
            f"## Pitfalls\n\n"
            f"Do not copy another profile's plugin or skills.\n\n"
            f"## Verification\n\n"
            f"The output matches the job sentence and cites official pages for knobs.\n"
        ),
    }


def scaffold_profile(args: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    try:
        payload = args or {}
        name = str(payload.get("name") or "").strip().lower()
        job = str(payload.get("job") or "").strip()
        author = str(payload.get("author") or "Hermes Agent Profile Library").strip()
        if not name or not job:
            return error("name and job are required")
        problem = _validate_name(name)
        if problem:
            return error(problem)
        gate = plan_store.evaluate_plan(name)
        if not gate.get("ok"):
            first = (gate.get("gaps") or ["plan incomplete"])[0]
            return error(f"check_plan is not ok for {name}: {first}")
        root = find_repo_root()
        if root is None:
            return error("library root not found (docs/PROFILE-PLAYBOOK.md missing)")
        dest = root / "agents" / name
        if dest.exists():
            return error(f"refusing to overwrite existing path: {dest}")
        files = _templates(name, job.replace('"', "'"), author.replace('"', "'"))
        written: list[str] = []
        dest.mkdir(parents=True, exist_ok=False)
        for rel, text in files.items():
            path = dest / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.name in {".env", "auth.json", "honcho.json"}:
                return error(f"refusing secret-shaped file {path.name}")
            path.write_text(text, encoding="utf-8")
            written.append(str(path.relative_to(root)))
        row = ledger.add_scaffold({"name": name, "path": str(dest), "files": written})
        return dump(
            {
                "ok": True,
                "name": name,
                "path": str(dest),
                "files": written,
                "scaffold_id": row.get("id"),
                "install": f"hermes profile install ./agents/{name} --alias",
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error(str(exc))
