#!/usr/bin/env python3
"""Structure checks for independent Hermes profiles. No live Hermes. No API keys."""

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
# Cross-profile ids this repo must never ship as a plugin or toolset.
_FORBIDDEN_CROSS_PROFILE_IDS = frozenset({"army", "army-runtime"})
_SKILL_SECTIONS = (
    "When to Use",
    "Quick Reference",
    "Procedure",
    "Pitfalls",
    "Verification",
)
_BANNED_DOC_PATHS = (
    ROOT / "docs" / "PROFILE-PLAYBOOK.md",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "WORKFLOW.md",
    ROOT / "docs" / "INTEGRATION.md",
    ROOT / "README.md",
    ROOT / "skills-tap" / "README.md",
    ROOT / ".cursor" / "rules" / "hermes-factory.mdc",
)
_BANNED_DOC_PATTERNS = (
    re.compile(r"\barmy-runtime\b", re.IGNORECASE),
    re.compile(r"\btoolset\s+army\b", re.IGNORECASE),
    re.compile(r"\bthe army\b", re.IGNORECASE),
    re.compile(r"\barmy\b", re.IGNORECASE),
)
_COLLAPSED_SURFACE_PATTERNS = (
    re.compile(r"\bplugin tools\b", re.IGNORECASE),
    re.compile(r"\bplugin tool\b", re.IGNORECASE),
    re.compile(r"plugin is the tools", re.IGNORECASE),
)
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


def check_playbook() -> None:
    playbook = ROOT / "docs" / "PROFILE-PLAYBOOK.md"
    if not playbook.is_file():
        fail("missing docs/PROFILE-PLAYBOOK.md (source of truth)")
        return
    text = playbook.read_text(encoding="utf-8")
    if "independent" not in text.lower():
        fail("PROFILE-PLAYBOOK.md must describe generating one independent profile")
    if "HERMES_HOME" not in text:
        fail("PROFILE-PLAYBOOK.md must define isolated HERMES_HOME")
    for url in (
        "https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills",
        "https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access",
        "https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api",
        "https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin",
    ):
        if url not in text:
            fail(f"PROFILE-PLAYBOOK.md must cite {url}")


def check_docs_voice() -> None:
    paths = list(_BANNED_DOC_PATHS)
    agents_root = ROOT / "agents"
    if agents_root.is_dir():
        paths.extend(agents_root.glob("*/SOUL.md"))
        paths.extend(agents_root.glob("*/README.md"))
        paths.extend(agents_root.glob("*/INTEGRATION.md"))
        paths.extend(agents_root.glob("*/skills/*/SKILL.md"))
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in _BANNED_DOC_PATTERNS:
            if pattern.search(text):
                fail(
                    f"{path.relative_to(ROOT)} names a cross-profile layer "
                    f"({pattern.pattern}); each profile is independent"
                )
                break
        for pattern in _COLLAPSED_SURFACE_PATTERNS:
            if pattern.search(text):
                fail(
                    f"{path.relative_to(ROOT)} collapses PLUGIN and TOOL "
                    f"({pattern.pattern}); say the plugin registers the tool"
                )
                break


def check_no_repo_root_plugin_package() -> None:
    root_plugins = ROOT / "plugins"
    if root_plugins.exists():
        fail(
            "repo-root plugins/ must not exist; live process code lives only "
            "in agents/<name>/plugins/<name>/"
        )


def check_no_foreign_research_bot_imports() -> None:
    skip_roots = {
        ROOT / "agents" / "research-bot" / "plugins" / "research-bot",
        ROOT / "tests",
    }
    needle = re.compile(
        r"^\s*(from|import)\s+research_bot_plugin\b",
        re.MULTILINE,
    )
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        if path == Path(__file__).resolve():
            continue
        if any(skip in path.parents or path.parent == skip for skip in skip_roots):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if needle.search(text):
            fail(
                f"{path.relative_to(ROOT)} imports research-bot; "
                "next profile has zero imports from that plugin"
            )


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
        return None
    end = text.find("\n---", 3)
    if end < 0:
        fail(f"{skill_md.relative_to(ROOT)} unclosed frontmatter")
        return None
    front = text[4:end]
    data = yaml.safe_load(front)
    if not isinstance(data, dict):
        fail(f"{skill_md.relative_to(ROOT)} frontmatter is not a mapping")
        return None
    if not data.get("name") or not data.get("description"):
        fail(f"{skill_md.relative_to(ROOT)} frontmatter needs name and description")
    hermes = (data.get("metadata") or {}).get("hermes")
    if not isinstance(hermes, dict):
        fail(f"{skill_md.relative_to(ROOT)} missing metadata.hermes")
        return None
    body = text[end + 4 :]
    for section in _SKILL_SECTIONS:
        if f"## {section}" not in body:
            fail(f"{skill_md.relative_to(ROOT)} missing required section ## {section}")
    return data


def _shipped_plugin_yamls(agent_dir: Path) -> list[Path]:
    plugins_root = agent_dir / "plugins"
    if not plugins_root.is_dir():
        return []
    return sorted(plugins_root.glob("*/plugin.yaml"))


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
    if plugin_name in _FORBIDDEN_CROSS_PROFILE_IDS:
        fail(f"{plugin_yaml.relative_to(ROOT)} plugin id {plugin_name!r} is not profile-local")
    if not manifest.get("provides_tools") and not manifest.get("provides_hooks"):
        fail(
            f"{plugin_yaml.relative_to(ROOT)} is a dummy plugin — "
            "ship tools and/or hooks, or do not ship the directory"
        )
    plugin_dir = plugin_yaml.parent
    if (plugin_dir / "plugin.json").is_file():
        fail(
            f"{plugin_dir.relative_to(ROOT)} ships plugin.json — "
            "Portable Agent Plugins v1 is not this factory's path"
        )
    if manifest.get("kind") in {"exclusive", "memory-provider", "memory"}:
        fail(
            f"{plugin_yaml.relative_to(ROOT)} must be a general plugin; "
            "Honcho is memory.provider"
        )
    for required_py in ("__init__.py", "schemas.py", "tools.py"):
        if not (plugin_dir / required_py).is_file():
            fail(f"{plugin_dir.relative_to(ROOT)} missing {required_py}")
    if not (plugin_dir / "__init__.py").is_file():
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
            "keep recipes in agents/<name>/skills/"
        )
    schemas_path = plugin_dir / "schemas.py"
    if schemas_path.is_file():
        schemas_text = schemas_path.read_text(encoding="utf-8")
        if '"type": "function"' in schemas_text or "'type': 'function'" in schemas_text:
            fail(
                f"{schemas_path.relative_to(ROOT)} must use the flat schema "
                "{name, description, parameters}"
            )
        for needle in ("When to call", "resolve_library", "docs_query", "cite_source"):
            if needle not in schemas_text:
                fail(f"{schemas_path.relative_to(ROOT)} must describe when to call {needle}")
    for path in plugin_dir.rglob("*"):
        if not path.is_file() or path.suffix in {".pyc"}:
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in _BANNED_DOC_PATTERNS:
            if pattern.search(text):
                fail(
                    f"{path.relative_to(ROOT)} names a cross-profile layer "
                    f"({pattern.pattern})"
                )
                break
        for pattern in _COLLAPSED_SURFACE_PATTERNS:
            if pattern.search(text):
                fail(
                    f"{path.relative_to(ROOT)} collapses PLUGIN and TOOL "
                    f"({pattern.pattern})"
                )
                break


def check_agent_plugin(agent_dir: Path, all_agent_names: set[str]) -> list[str]:
    """Return enabled plugin ids. A profile with no plugin is valid."""
    config_path = agent_dir / "config.yaml"
    config = load_yaml(config_path) if config_path.is_file() else {}
    if not isinstance(config, dict):
        config = {}
    if agent_dir.name == "research-bot" and config.get("system_message"):
        fail(
            f"{agent_dir.name} must not set config system_message "
            "(cached); turn-varying contract goes in pre_llm_call"
        )
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
    for name in enabled_names:
        if name in OUROBOROS_PLUGIN_NAMES:
            fail(f"{agent_dir.name} plugins.enabled collides with ouroboros name {name!r}")
        if name in _FORBIDDEN_CROSS_PROFILE_IDS:
            fail(f"{agent_dir.name} plugins.enabled {name!r} is not profile-local")
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
        if dirname in all_agent_names and dirname != agent_dir.name:
            fail(
                f"{agent_dir.name} ships plugins/{dirname}/ — that plugin "
                f"belongs to profile {dirname!r}. Next profile starts empty."
            )
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
    for forbidden in _FORBIDDEN_CROSS_PROFILE_IDS:
        if forbidden in bundled:
            fail(f"{agent_dir.name} custom_toolsets must not include {forbidden!r}")
    for name in enabled_names:
        if name not in bundled:
            fail(
                f"{agent_dir.name} custom_toolsets must include this profile's "
                f"toolset {name!r}"
            )
    if agent_dir.name != "research-bot":
        if "research-bot" in enabled_names:
            fail(
                f"{agent_dir.name} must not enable the research-bot plugin; "
                "next profile writes its own plugin"
            )
        if "research-bot" in bundled:
            fail(
                f"{agent_dir.name} must not enable toolset research-bot; "
                "that toolset is research-bot only"
            )

    return enabled_names


def check_agent(agent_dir: Path, all_agent_names: set[str]) -> None:
    check_distribution(agent_dir)
    for required in ("SOUL.md", "config.yaml", "README.md", "INTEGRATION.md", ".gitignore"):
        if not (agent_dir / required).is_file():
            fail(f"{agent_dir.name} missing {required}")
    factory_integration = ROOT / "docs" / "INTEGRATION.md"
    if factory_integration.is_file() and agent_dir.name == "research-bot":
        factory_text = factory_integration.read_text(encoding="utf-8")
        for url in (
            "https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin",
        ):
            if url not in factory_text:
                fail(f"{factory_integration.relative_to(ROOT)} must cite {url}")
    integration = agent_dir / "INTEGRATION.md"
    if integration.is_file() and agent_dir.name == "research-bot":
        integration_text = integration.read_text(encoding="utf-8")
        for url in (
            "https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/plugins",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin",
        ):
            if url not in integration_text:
                fail(f"{integration.relative_to(ROOT)} must cite {url}")
        if "system_message" in integration_text and "pre_llm_call" not in integration_text:
            fail(f"{integration.relative_to(ROOT)} must lock pre_llm_call for turn-varying text")
        if "Three surfaces" not in integration_text:
            fail(
                f"{integration.relative_to(ROOT)} must keep SKILL, TOOL, and "
                "PLUGIN as three official surfaces"
            )
        for heading in (
            "Settled: memory",
            "Profile identity + skills index",
            "Dedicated native plugin",
            "MCP as a backend",
            "Agent loop + hooks",
            "ctx.llm",
            "Subagent constraints",
        ):
            if heading not in integration_text:
                fail(f"{integration.relative_to(ROOT)} must plan the execution join ({heading})")
        honcho_hits = len(re.findall(r"honcho", integration_text, re.IGNORECASE))
        if honcho_hits > 3:
            fail(
                f"{integration.relative_to(ROOT)} restates Honcho ({honcho_hits} hits); "
                "keep one settled block"
            )
    soul = agent_dir / "SOUL.md"
    if soul.is_file() and agent_dir.name == "research-bot":
        soul_text = soul.read_text(encoding="utf-8")
        for needle in ("resolve_library", "docs_query", "cite_source", "mcp_*"):
            if needle in soul_text:
                fail(
                    f"{soul.relative_to(ROOT)} is identity only; "
                    f"do not put {needle} procedures in SOUL"
                )
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
        for host in hosts.values():
            if isinstance(host, dict) and host.get("pinUserPeer") is not True:
                fail(f"{example.relative_to(ROOT)} pinUserPeer must be true (gateway-only)")
    enabled_names = check_agent_plugin(agent_dir, all_agent_names)
    other_profiles = all_agent_names - {agent_dir.name}
    skills = agent_dir / "skills"
    if skills.is_dir():
        skill_files = list(skills.glob("*/SKILL.md"))
        if not skill_files:
            fail(f"{agent_dir.name}/skills has no SKILL.md files")
        for skill_md in skill_files:
            front = check_skill(skill_md)
            if not isinstance(front, dict):
                continue
            hermes = (front.get("metadata") or {}).get("hermes") or {}
            required = [str(item) for item in (hermes.get("requires_toolsets") or [])]
            tools = hermes.get("requires_tools") or []
            for foreign in other_profiles:
                if foreign in required:
                    fail(
                        f"{skill_md.relative_to(ROOT)} requires toolset {foreign!r} "
                        "from another profile"
                    )
            for name in enabled_names:
                if name not in required:
                    fail(
                        f"{skill_md.relative_to(ROOT)} must set "
                        f"metadata.hermes.requires_toolsets including {name!r}"
                    )
            if enabled_names and not tools:
                fail(
                    f"{skill_md.relative_to(ROOT)} must set "
                    "metadata.hermes.requires_tools for tools this plugin registers"
                )
            for forbidden in _FORBIDDEN_CROSS_PROFILE_IDS:
                if forbidden in required:
                    fail(
                        f"{skill_md.relative_to(ROOT)} requires_toolsets "
                        f"must not include {forbidden!r}"
                    )
            dumped_front = yaml.safe_dump(front)
            if "CONTEXT7_API_KEY" in dumped_front:
                fail(
                    f"{skill_md.relative_to(ROOT)} must not declare CONTEXT7_API_KEY; "
                    "ctx.call_mcp owns that"
                )
            hermes_blueprint = hermes.get("blueprint")
            if hermes_blueprint:
                fail(
                    f"{skill_md.relative_to(ROOT)} must not ship a blueprint "
                    "unless a scheduled job was requested"
                )
            if agent_dir.name == "research-bot":
                tool_names = [str(item) for item in tools]
                for needed in ("resolve_library", "docs_query", "cite_source"):
                    if needed not in tool_names:
                        fail(
                            f"{skill_md.relative_to(ROOT)} requires_tools must "
                            f"include {needed!r}"
                        )
                related = [str(item) for item in (hermes.get("related_skills") or [])]
                skill_name = str(front.get("name") or skill_md.parent.name)
                expected_related = {
                    "literature-review",
                    "source-triage",
                    "claim-check",
                } - {skill_name}
                for other in sorted(expected_related):
                    if other not in related:
                        fail(
                            f"{skill_md.relative_to(ROOT)} related_skills must "
                            f"include {other!r}"
                        )
                body = skill_md.read_text(encoding="utf-8")
                for named in ("resolve_library", "docs_query", "cite_source", "mcp_*"):
                    if named not in body:
                        fail(
                            f"{skill_md.relative_to(ROOT)} Procedure must name {named}"
                        )


def main() -> int:
    agents_root = ROOT / "agents"
    if not agents_root.is_dir():
        fail("missing agents/")
        return 1
    check_playbook()
    check_docs_voice()
    check_no_repo_root_plugin_package()
    check_no_foreign_research_bot_imports()
    check_no_secret_files()
    check_no_literal_keys()
    agent_dirs = sorted(
        path for path in agents_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    if not agent_dirs:
        fail("no agent directories under agents/")
    all_agent_names = {path.name for path in agent_dirs}
    for agent_dir in agent_dirs:
        check_agent(agent_dir, all_agent_names)
    if errors:
        print(f"{len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"ok: {len(agent_dirs)} independent profile(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
