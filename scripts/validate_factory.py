#!/usr/bin/env python3
"""Structure checks for this factory. No live Hermes. No API keys."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
RESERVED = {"hermes", "test", "tmp", "root", "sudo"}
SECRET_NAMES = {
    ".env",
    "auth.json",
    "honcho.json",
}
SECRET_VALUE_RE = re.compile(
    r"(sk-[A-Za-z0-9]{10,}|hch-[A-Za-z0-9]{10,}|CONTEXT7_API_KEY\s*[:=]\s*['\"][^$\s{])"
)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    errors.append(message)


errors: list[str] = []


def load_yaml(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def check_no_secret_files() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.name in SECRET_NAMES:
            fail(f"secret-shaped file must not be committed: {path.relative_to(ROOT)}")
        if path.suffix == ".env":
            fail(f"env file must not be committed: {path.relative_to(ROOT)}")


def check_no_literal_keys() -> None:
    skip_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pyc"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in skip_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SECRET_VALUE_RE.search(text):
            fail(f"possible literal secret in {path.relative_to(ROOT)}")


def check_distribution(agent_dir: Path) -> None:
    manifest_path = agent_dir / "distribution.yaml"
    if not manifest_path.is_file():
        fail(f"missing {manifest_path.relative_to(ROOT)}")
        return
    data = load_yaml(manifest_path)
    if not isinstance(data, dict):
        fail(f"{manifest_path.relative_to(ROOT)} is not a mapping")
        return
    name = data.get("name")
    if not isinstance(name, str) or not name:
        fail(f"{manifest_path.relative_to(ROOT)} missing name")
        return
    if name in RESERVED:
        fail(f"reserved profile name: {name}")
    if name != agent_dir.name:
        fail(f"distribution name {name!r} != directory {agent_dir.name!r}")
    for key in ("version", "description", "author"):
        if not data.get(key):
            fail(f"{manifest_path.relative_to(ROOT)} missing {key}")
    env_requires = data.get("env_requires") or []
    if not isinstance(env_requires, list):
        fail(f"{manifest_path.relative_to(ROOT)} env_requires must be a list")
        return
    for item in env_requires:
        if not isinstance(item, dict) or "name" not in item:
            fail(f"{manifest_path.relative_to(ROOT)} env_requires entry missing name")
            continue
        if "required" not in item:
            fail(f"{manifest_path.relative_to(ROOT)} {item['name']} missing required flag")
        if not isinstance(item.get("required"), bool):
            fail(f"{manifest_path.relative_to(ROOT)} {item['name']} required must be bool")


def check_skill(skill_md: Path) -> None:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail(f"{skill_md.relative_to(ROOT)} missing YAML frontmatter")
        return
    end = text.find("\n---", 3)
    if end < 0:
        fail(f"{skill_md.relative_to(ROOT)} unclosed frontmatter")
        return
    front = text[4:end]
    data = yaml.safe_load(front)
    if not isinstance(data, dict):
        fail(f"{skill_md.relative_to(ROOT)} frontmatter is not a mapping")
        return
    if not data.get("name") or not data.get("description"):
        fail(f"{skill_md.relative_to(ROOT)} frontmatter needs name and description")
    hermes = (data.get("metadata") or {}).get("hermes")
    if not isinstance(hermes, dict):
        fail(f"{skill_md.relative_to(ROOT)} missing metadata.hermes")


def check_agent(agent_dir: Path) -> None:
    check_distribution(agent_dir)
    for required in ("SOUL.md", "config.yaml", "README.md", ".gitignore"):
        if not (agent_dir / required).is_file():
            fail(f"{agent_dir.name} missing {required}")
    mcp = agent_dir / "mcp.json"
    if mcp.is_file():
        payload = json.loads(mcp.read_text(encoding="utf-8"))
        if "mcp_servers" not in payload:
            fail(f"{mcp.relative_to(ROOT)} missing mcp_servers")
        dumped = json.dumps(payload)
        if "sk-" in dumped or "hch-" in dumped:
            fail(f"{mcp.relative_to(ROOT)} looks like it contains a literal key")
    example = agent_dir / "honcho.json.example"
    if example.is_file():
        payload = json.loads(example.read_text(encoding="utf-8"))
        api_key = payload.get("apiKey")
        if isinstance(api_key, str) and api_key and not api_key.startswith("your-"):
            fail(f"{example.relative_to(ROOT)} must not contain a real apiKey")
        hosts = payload.get("hosts")
        if not isinstance(hosts, dict) or not hosts:
            fail(f"{example.relative_to(ROOT)} missing hosts")
    skills = agent_dir / "skills"
    if skills.is_dir():
        skill_files = list(skills.glob("*/SKILL.md"))
        if not skill_files:
            fail(f"{agent_dir.name}/skills has no SKILL.md files")
        for skill_md in skill_files:
            check_skill(skill_md)


def main() -> int:
    agents_root = ROOT / "agents"
    if not agents_root.is_dir():
        fail("missing agents/")
        return 1
    check_no_secret_files()
    check_no_literal_keys()
    agent_dirs = sorted(p for p in agents_root.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not agent_dirs:
        fail("no agent directories under agents/")
    for agent_dir in agent_dirs:
        check_agent(agent_dir)
    if errors:
        print(f"{len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"ok: {len(agent_dirs)} agent(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
