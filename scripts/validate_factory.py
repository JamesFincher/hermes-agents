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
OUROBOROS_PLUGIN_NAMES = {
    "echo",
    "archive",
    "seatbelt",
    "council",
    "autopilot",
    "forge",
}
ARMY_PLUGIN = "army-runtime"
ARMY_TOOLSET = "army"
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


def check_skill(skill_md: Path) -> dict | None:
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
        return
    return data


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
    check_agent_plugin(agent_dir)
    skills = agent_dir / "skills"
    if skills.is_dir():
        skill_files = list(skills.glob("*/SKILL.md"))
        if not skill_files:
            fail(f"{agent_dir.name}/skills has no SKILL.md files")
        for skill_md in skill_files:
            front = check_skill(skill_md)
            if isinstance(front, dict):
                hermes = (front.get("metadata") or {}).get("hermes") or {}
                required = hermes.get("requires_toolsets") or []
                if ARMY_TOOLSET not in required:
                    fail(
                        f"{skill_md.relative_to(ROOT)} must set "
                        f"metadata.hermes.requires_toolsets including {ARMY_TOOLSET!r}"
                    )
                if not hermes.get("requires_tools"):
                    fail(
                        f"{skill_md.relative_to(ROOT)} must set "
                        "metadata.hermes.requires_tools for army tools"
                    )


def _shipped_plugin_yamls(agent_dir: Path) -> list[Path]:
    plugins_root = agent_dir / "plugins"
    if not plugins_root.is_dir():
        return []
    return sorted(plugins_root.glob("*/plugin.yaml"))


def _file_fingerprint(root: Path) -> dict[str, str]:
    skip = {"__pycache__", ".pyc"}
    found: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in skip or part.endswith(".pyc") for part in path.parts):
            continue
        found[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
    return found


def check_one_plugin_manifest(plugin_yaml: Path, expected_dirname: str) -> None:
    manifest = load_yaml(plugin_yaml)
    if not isinstance(manifest, dict):
        fail(f"{plugin_yaml.relative_to(ROOT)} is not a mapping")
        return
    plugin_name = manifest.get("name")
    if plugin_name != expected_dirname:
        fail(
            f"{plugin_yaml.relative_to(ROOT)} name {plugin_name!r} "
            f"!= directory {expected_dirname!r}"
        )
    if plugin_name in OUROBOROS_PLUGIN_NAMES:
        fail(f"forbidden plugin name: {plugin_name!r}")
    if not manifest.get("provides_tools") and not manifest.get("provides_hooks"):
        fail(
            f"{plugin_yaml.relative_to(ROOT)} is a dummy plugin — "
            "ship tools and/or hooks, or do not ship the directory"
        )
    plugin_dir = plugin_yaml.parent
    if not (plugin_dir / "__init__.py").is_file():
        fail(f"{plugin_dir.relative_to(ROOT)} missing __init__.py")
        return
    init_text = (plugin_dir / "__init__.py").read_text(encoding="utf-8")
    if "def register(" not in init_text:
        fail(f"{plugin_dir.relative_to(ROOT)}/__init__.py missing register(ctx)")
    if "ctx.register_skill" in init_text or "register_skill(" in init_text:
        fail(
            f"{plugin_dir.relative_to(ROOT)} must not register plugin-bundled "
            "skills for the primary library"
        )
    if list(plugin_dir.glob("skills/*/SKILL.md")):
        fail(
            f"{plugin_dir.relative_to(ROOT)} ships plugin-bundled skills; "
            "keep recipes in agents/*/skills/ or skills-tap/"
        )


def check_army_runtime_source() -> None:
    source = ROOT / "plugins" / ARMY_PLUGIN
    plugin_yaml = source / "plugin.yaml"
    if not plugin_yaml.is_file():
        fail(f"missing factory source {plugin_yaml.relative_to(ROOT)}")
        return
    check_one_plugin_manifest(plugin_yaml, ARMY_PLUGIN)
    manifest = load_yaml(plugin_yaml)
    if isinstance(manifest, dict):
        tools = manifest.get("provides_tools") or []
        if "source_ledger_cite" not in tools:
            fail("army-runtime must provide source_ledger_cite (structured citation)")


def check_agent_plugin(agent_dir: Path) -> None:
    config_path = agent_dir / "config.yaml"
    config = load_yaml(config_path) if config_path.is_file() else {}
    if not isinstance(config, dict):
        config = {}
    plugins_cfg = config.get("plugins") or {}
    if not isinstance(plugins_cfg, dict):
        plugins_cfg = {}
    enabled = plugins_cfg.get("enabled") or []
    if not isinstance(enabled, list):
        fail(f"{agent_dir.name} plugins.enabled must be a list")
        enabled = []
    enabled_names = [str(name) for name in enabled]
    if "honcho" in enabled_names:
        fail(f"{agent_dir.name}: Honcho is memory.provider, not plugins.enabled")
    if ARMY_PLUGIN not in enabled_names:
        fail(f"{agent_dir.name} plugins.enabled must include {ARMY_PLUGIN!r}")
    for name in enabled_names:
        if name in OUROBOROS_PLUGIN_NAMES:
            fail(f"{agent_dir.name} plugins.enabled collides with ouroboros name {name!r}")
        plugin_yaml = agent_dir / "plugins" / name / "plugin.yaml"
        if not plugin_yaml.is_file():
            fail(
                f"{agent_dir.name} enables {name!r} but missing "
                f"{plugin_yaml.relative_to(ROOT)}"
            )

    shipped = _shipped_plugin_yamls(agent_dir)
    for plugin_yaml in shipped:
        dirname = plugin_yaml.parent.name
        check_one_plugin_manifest(plugin_yaml, dirname)
        if dirname not in enabled_names:
            fail(
                f"{agent_dir.name} ships {plugin_yaml.parent.relative_to(ROOT)} "
                "but does not list it in plugins.enabled (dead garnish)"
            )

    if shipped:
        dist = load_yaml(agent_dir / "distribution.yaml")
        if isinstance(dist, dict):
            owned = dist.get("distribution_owned") or []
            if "plugins" not in owned:
                fail(
                    f"{agent_dir.name} ships plugins/ but distribution_owned "
                    "does not claim plugins (not in the official default owned set)"
                )

    custom = config.get("custom_toolsets") or {}
    bundled: list[str] = []
    if isinstance(custom, dict):
        for names in custom.values():
            if isinstance(names, list):
                bundled.extend(str(item) for item in names)
    if ARMY_TOOLSET not in bundled:
        fail(f"{agent_dir.name} custom_toolsets must include toolset {ARMY_TOOLSET!r}")

    factory = ROOT / "plugins" / ARMY_PLUGIN
    consumer = agent_dir / "plugins" / ARMY_PLUGIN
    if factory.is_dir() and consumer.is_dir():
        factory_files = _file_fingerprint(factory)
        consumer_files = _file_fingerprint(consumer)
        if factory_files != consumer_files:
            fail(
                f"{agent_dir.name}/plugins/{ARMY_PLUGIN} must match "
                f"factory plugins/{ARMY_PLUGIN} — edit the factory source and recopy"
            )
    elif factory.is_dir():
        fail(f"{agent_dir.name} missing copy of plugins/{ARMY_PLUGIN}")


def main() -> int:
    agents_root = ROOT / "agents"
    if not agents_root.is_dir():
        fail("missing agents/")
        return 1
    check_no_secret_files()
    check_no_literal_keys()
    check_army_runtime_source()
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
