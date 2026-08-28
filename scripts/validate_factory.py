#!/usr/bin/env python3
"""Structure checks for the Hermes Agent Profile Library. No live Hermes. No API keys."""

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


_PRODUCT_NAME = "Hermes Agent Profile Library"
_PRODUCT_NAME_PATHS = (
    ROOT / "docs" / "PROFILE-PLAYBOOK.md",
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / "docs" / "WORKFLOW.md",
)


def check_product_name() -> None:
    for path in _PRODUCT_NAME_PATHS:
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if _PRODUCT_NAME not in text:
            fail(f"{path.relative_to(ROOT)} must name the product {_PRODUCT_NAME!r}")


def check_playbook() -> None:
    playbook = ROOT / "docs" / "PROFILE-PLAYBOOK.md"
    if not playbook.is_file():
        fail("missing docs/PROFILE-PLAYBOOK.md (source of truth)")
        return
    text = playbook.read_text(encoding="utf-8")
    if "Hermes Agent Profile Library" not in text:
        fail("PROFILE-PLAYBOOK.md must name the product Hermes Agent Profile Library")
    if "nine surfaces" not in text.lower():
        fail("PROFILE-PLAYBOOK.md must specify the nine surfaces")
    if "primary identity" not in text.lower():
        fail("PROFILE-PLAYBOOK.md must lock SOUL as primary identity")
    if "the plugin registers the tool" not in text:
        fail("PROFILE-PLAYBOOK.md must say the plugin registers the tool")
    if "HERMES_HOME" not in text:
        fail("PROFILE-PLAYBOOK.md must define isolated HERMES_HOME")
    if "HONEST-LIMITS.md" not in text:
        fail("PROFILE-PLAYBOOK.md must require HONEST-LIMITS.md")
    if ">=0.13.0" not in text:
        fail("PROFILE-PLAYBOOK.md must keep hermes_requires at an official example range")
    if "0.14.0" in text and "not an invented" not in text:
        fail("PROFILE-PLAYBOOK.md must not invent hermes_requires 0.14.0")
    if "hermes profile install ./agents/" not in text:
        fail("PROFILE-PLAYBOOK.md must lock path install")
    if "repo-root `distribution.yaml`" not in text and "repo-root distribution.yaml" not in text:
        fail("PROFILE-PLAYBOOK.md must forbid a repo-root distribution.yaml until official")
    if "[UNV]" not in text:
        fail("PROFILE-PLAYBOOK.md must keep the §11 index line [UNV] / not shipped")
    if "plugins doctor" not in text.lower():
        fail("PROFILE-PLAYBOOK.md must record the official STOP: no plugins doctor")
    leftovers = (
        "source_ledger_add",
        "source_ledger_list",
        "source_ledger_check",
        "source_ledger_*",
        "plugins/research-bot/",
        "requires_toolsets: [research-bot]",
        "plugins.enabled: [research-bot]",
    )
    for needle in leftovers:
        if needle in text:
            fail(
                f"PROFILE-PLAYBOOK.md still names {needle!r} as current. "
                "HDR v2 uses evidence_* / claim_verify and agents/<name>/plugins/<plugin-id>/"
            )


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
        for line in text.splitlines():
            lower = line.lower()
            stop_line = "never reintroduce" in lower or (
                lower.lstrip().startswith(">") and "stop" in lower
            )
            for pattern in _BANNED_DOC_PATTERNS:
                if pattern.search(line) and not stop_line:
                    fail(
                        f"{path.relative_to(ROOT)} names a cross-profile layer "
                        f"({pattern.pattern}); each profile is independent"
                    )
                    break
            else:
                for pattern in _COLLAPSED_SURFACE_PATTERNS:
                    if pattern.search(line) and "never" not in lower:
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
            "in agents/<name>/plugins/<plugin-id>/"
        )


def check_no_foreign_research_bot_imports() -> None:
    skip_roots = {
        ROOT / "agents" / "research-bot" / "plugins" / "research-bot",
        ROOT / "agents" / "research-bot" / "plugins" / "hdr",
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
            "Portable Agent Plugins v1 is not this library's path"
        )
    if manifest.get("kind") in {"exclusive", "memory-provider", "memory"}:
        fail(
            f"{plugin_yaml.relative_to(ROOT)} must be a general plugin; "
            "Honcho is memory.provider"
        )
    for required_py in ("__init__.py", "schemas.py"):
        if not (plugin_dir / required_py).is_file():
            fail(f"{plugin_dir.relative_to(ROOT)} missing {required_py}")
    tools_ok = (plugin_dir / "tools.py").is_file() or (plugin_dir / "tools" / "__init__.py").is_file()
    if not tools_ok:
        fail(f"{plugin_dir.relative_to(ROOT)} missing tools.py or tools/__init__.py")
    if (plugin_dir / "tools.py").is_file() and (plugin_dir / "tools" / "__init__.py").is_file():
        fail(f"{plugin_dir.relative_to(ROOT)} cannot ship both tools.py and tools/")
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
        if "When to call" not in schemas_text:
            fail(f"{schemas_path.relative_to(ROOT)} must describe when to call each tool")
        if expected_dirname == "hdr":
            for needle in ("resolve_library", "docs_query", "cite_source"):
                if needle not in schemas_text:
                    fail(f"{schemas_path.relative_to(ROOT)} must describe when to call {needle}")
        manifest_tools = []
        if isinstance(manifest, dict):
            raw_tools = manifest.get("provides_tools") or []
            if isinstance(raw_tools, list):
                manifest_tools = [str(item) for item in raw_tools]
        for tool_name in manifest_tools:
            if tool_name not in schemas_text:
                fail(
                    f"{schemas_path.relative_to(ROOT)} must describe when to call {tool_name}"
                )
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
    if agent_dir.name == "research-bot":
        web = config.get("web") if isinstance(config.get("web"), dict) else {}
        if web.get("search_backend") != "searxng":
            fail(f"{agent_dir.name} web.search_backend must be 'searxng'")
        if web.get("extract_backend") != "firecrawl":
            fail(f"{agent_dir.name} web.extract_backend must be 'firecrawl'")
        if web.get("keyless_fallback") is not True:
            fail(f"{agent_dir.name} web.keyless_fallback must be true (HDR v2 degrade, not die)")
        if web.get("keyless_rescue") is not True:
            fail(f"{agent_dir.name} web.keyless_rescue must be true")
        if web.get("search_backend") == "searxng" and agent_dir.name == "research-bot":
            bundled = []
            custom = config.get("custom_toolsets") or {}
            if isinstance(custom, dict):
                for names in custom.values():
                    if isinstance(names, list):
                        bundled.extend(str(item) for item in names)
            for needed in (
                "web",
                "browser",
                "vision",
                "file",
                "terminal",
                "code_execution",
                "skills",
                "memory",
                "session_search",
                "todo",
                "clarify",
                "delegation",
                "cronjob",
                "hdr",
            ):
                if needed not in bundled:
                    fail(f"{agent_dir.name} custom_toolsets.research must include {needed!r}")
            if "moa" in bundled:
                fail(
                    f"{agent_dir.name} must not list toolset moa "
                    "(official: no moa toolset; MoA is a provider)"
                )
            plugins_enabled = (config.get("plugins") or {}).get("enabled") or []
            if plugins_enabled != ["hdr"]:
                fail(f"{agent_dir.name} plugins.enabled must be [hdr]")
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
        if "hdr" in enabled_names or "hdr" in bundled:
            fail(
                f"{agent_dir.name} must not enable plugin or toolset hdr; "
                "hdr stays on research-bot only"
            )

    return enabled_names


def check_agent(agent_dir: Path, all_agent_names: set[str]) -> None:
    check_distribution(agent_dir)
    for required in ("SOUL.md", "config.yaml", "README.md", "INTEGRATION.md", ".gitignore"):
        if not (agent_dir / required).is_file():
            fail(f"{agent_dir.name} missing {required}")
    if agent_dir.name != "research-bot" and not (agent_dir / "HONEST-LIMITS.md").is_file():
        fail(f"{agent_dir.name} missing HONEST-LIMITS.md (playbook law 11)")
    if agent_dir.name == "research-bot" and not (agent_dir / ".env.EXAMPLE").is_file():
        fail("research-bot missing .env.EXAMPLE (post-install copy source)")
    if agent_dir.name == "inception" and not (agent_dir / ".env.EXAMPLE").is_file():
        fail("inception missing .env.EXAMPLE (post-install copy source)")
    factory_integration = ROOT / "docs" / "INTEGRATION.md"
    if factory_integration.is_file() and agent_dir.name == "research-bot":
        factory_text = factory_integration.read_text(encoding="utf-8")
        for url in (
            "https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin",
            "https://hermes-agent.nousresearch.com/docs/user-guide/features/tools",
            "https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference",
            "https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin",
            "https://hermes-agent.nousresearch.com/docs/user-guide/configuration",
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
            "https://hermes-agent.nousresearch.com/docs/user-guide/features/tools",
            "https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference",
            "https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search",
            "https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin",
            "https://hermes-agent.nousresearch.com/docs/user-guide/configuration",
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
        if agent_dir.name == "research-bot":
            present = {path.parent.name for path in skill_files}
            expected = {
                "deep-research-run",
                "source-triage",
                "claim-audit",
                "literature-sweep",
                "web-fallback-fetch",
            }
            missing = expected - present
            extra = present - expected
            if missing:
                fail(f"{agent_dir.name} missing HDR skills: {sorted(missing)}")
            if extra:
                fail(f"{agent_dir.name} unexpected skills: {sorted(extra)}")
        if agent_dir.name == "inception":
            present = {path.parent.name for path in skill_files}
            expected = {"author-profile", "probe-knob", "review-profile"}
            missing = expected - present
            extra = present - expected
            if missing:
                fail(f"{agent_dir.name} missing factory skills: {sorted(missing)}")
            if extra:
                fail(f"{agent_dir.name} unexpected skills: {sorted(extra)}")
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
                skill_name = str(front.get("name") or skill_md.parent.name)
                expected_skills = {
                    "deep-research-run",
                    "source-triage",
                    "claim-audit",
                    "literature-sweep",
                    "web-fallback-fetch",
                }
                if skill_name not in expected_skills:
                    fail(
                        f"{skill_md.relative_to(ROOT)} unexpected skill {skill_name!r}; "
                        f"HDR ships {sorted(expected_skills)}"
                    )
                tool_names = [str(item) for item in tools]
                required_by_skill = {
                    "deep-research-run": [
                        "research_plan",
                        "gap_scan",
                        "cite_source",
                        "delegate_task",
                        "worker_brief",
                        "worker_harvest",
                        "claim_verify",
                        "conflict_report",
                        "evidence_search",
                        "evidence_read",
                    ],
                    "source-triage": ["evidence_add", "evidence_search"],
                    "claim-audit": ["claim_verify", "cite_source"],
                    "literature-sweep": ["scholar_search", "evidence_add"],
                    "web-fallback-fetch": ["archive_lookup", "evidence_add"],
                }
                for needed in required_by_skill.get(skill_name, []):
                    if needed not in tool_names:
                        fail(
                            f"{skill_md.relative_to(ROOT)} requires_tools must "
                            f"include {needed!r}"
                        )
                if skill_name == "deep-research-run":
                    for needed_set in ("hdr", "delegation", "web"):
                        if needed_set not in required:
                            fail(
                                f"{skill_md.relative_to(ROOT)} requires_toolsets "
                                f"must include {needed_set!r}"
                            )
                if skill_name == "web-fallback-fetch":
                    fallback = [str(item) for item in (hermes.get("fallback_for_tools") or [])]
                    if "web_extract" not in fallback:
                        fail(
                            f"{skill_md.relative_to(ROOT)} must set "
                            "fallback_for_tools: [web_extract]"
                        )
                body = skill_md.read_text(encoding="utf-8")
                if "mcp_*" not in body:
                    fail(
                        f"{skill_md.relative_to(ROOT)} must tell the model not "
                        "to call raw mcp_* tools"
                    )
                if skill_name == "source-triage" and "${HERMES_SKILL_DIR}" not in body:
                    fail(f"{skill_md.relative_to(ROOT)} must invoke scripts via ${{HERMES_SKILL_DIR}}")
                if skill_name == "claim-audit" and "source_ledger_check" not in body:
                    fail(
                        f"{skill_md.relative_to(ROOT)} must state that "
                        "source_ledger_check is gone"
                    )
                if skill_name == "literature-sweep":
                    _check_literature_sweep_env(skill_md, front, hermes)
                    if "vision_analyze" not in body:
                        fail(
                            f"{skill_md.relative_to(ROOT)} must name the "
                            "scanned-PDF path (rasterize + vision_analyze)"
                        )
                    if "deep-research-run" not in body.lower() and "deep-research-run" not in body:
                        fail(
                            f"{skill_md.relative_to(ROOT)} must send academic "
                            "surveys to deep-research-run"
                        )
                if skill_name == "deep-research-run":
                    if '"action":"steer"' not in body and '{"action":"steer"' not in body:
                        fail(f"{skill_md.relative_to(ROOT)} must teach steer")
                    if "delegation.model" not in body:
                        fail(
                            f"{skill_md.relative_to(ROOT)} must remind the "
                            "operator to set delegation.model on the host"
                        )
                    if "scholar_search" not in body or "vision_analyze" not in body:
                        fail(
                            f"{skill_md.relative_to(ROOT)} must write the "
                            "§9 retrieval ladders into Procedure"
                        )
                if skill_name == "web-fallback-fetch":
                    fetch_script = skill_md.parent / "scripts" / "fetch_page.py"
                    if not fetch_script.is_file():
                        fail(f"{fetch_script.relative_to(ROOT)} missing")
                    else:
                        fetch_text = fetch_script.read_text(encoding="utf-8")
                        if "curl" not in fetch_text or "readable" not in fetch_text.lower():
                            fail(
                                f"{fetch_script.relative_to(ROOT)} must use "
                                "curl and a readability pass"
                            )
                        if "web.archive.org" not in fetch_text:
                            fail(
                                f"{fetch_script.relative_to(ROOT)} must try Wayback"
                            )
    _check_hdr_script_twins(agent_dir)
    _check_inception_join(agent_dir)


def collect_agent_errors(agent_dir: Path) -> list[str]:
    """Return validator gaps for one profile directory. Does not print."""
    saved = list(errors)
    errors.clear()
    try:
        agents_root = ROOT / "agents"
        all_names = set()
        if agents_root.is_dir():
            all_names = {
                path.name
                for path in agents_root.iterdir()
                if path.is_dir() and not path.name.startswith(".")
            }
        all_names.add(agent_dir.name)
        check_agent(agent_dir, all_names)
        return list(errors)
    finally:
        errors.clear()
        errors.extend(saved)


def _check_inception_join(agent_dir: Path) -> None:
    if agent_dir.name != "inception":
        return
    integration = agent_dir / "INTEGRATION.md"
    if integration.is_file():
        text = integration.read_text(encoding="utf-8")
        for heading in (
            "Nine surfaces",
            "Settled: memory",
            "Custom surface",
            "MCP as a backend",
        ):
            if heading not in text:
                fail(f"{integration.relative_to(ROOT)} must plan the join ({heading})")
        if "docs_resolve" not in text or "scaffold_profile" not in text:
            fail(f"{integration.relative_to(ROOT)} must list the tools the inception plugin registers")
        if "hdr" in text and "must not" not in text.lower():
            fail(f"{integration.relative_to(ROOT)} must not enable hdr")
    soul = agent_dir / "SOUL.md"
    if soul.is_file():
        soul_text = soul.read_text(encoding="utf-8")
        for needle in ("docs_resolve", "docs_ask", "scaffold_profile", "mcp_*"):
            if needle in soul_text:
                fail(
                    f"{soul.relative_to(ROOT)} is identity only; "
                    f"do not put {needle} procedures in SOUL"
                )
    canvas = ROOT / "docs" / "profiles" / "inception-canvas.md"
    if not canvas.is_file():
        fail("inception missing docs/profiles/inception-canvas.md")
    spec = ROOT / "docs" / "profiles" / "inception-spec.md"
    if not spec.is_file():
        fail("inception missing docs/profiles/inception-spec.md")
    eval_tasks = agent_dir / "evals" / "tasks.jsonl"
    if not eval_tasks.is_file():
        fail("inception missing evals/tasks.jsonl")
    else:
        rows = [line for line in eval_tasks.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) < 8:
            fail("inception evals/tasks.jsonl must have at least 8 frozen tasks")
        adversarial = 0
        for line in rows:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                fail("inception evals/tasks.jsonl has a non-JSON line")
                continue
            if payload.get("adversarial"):
                adversarial += 1
        if adversarial < 2:
            fail("inception evals/tasks.jsonl must include at least 2 adversarial tasks")
    if not (agent_dir / "evals" / "rubric.md").is_file():
        fail("inception missing evals/rubric.md")
    config = load_yaml(agent_dir / "config.yaml") if (agent_dir / "config.yaml").is_file() else {}
    if isinstance(config, dict):
        web = config.get("web") if isinstance(config.get("web"), dict) else {}
        if web.get("search_backend") != "searxng":
            fail("inception web.search_backend must be 'searxng' when the profile uses the web")
        if web.get("extract_backend") != "firecrawl":
            fail("inception web.extract_backend must be 'firecrawl'")
        if web.get("keyless_fallback") is not True:
            fail("inception web.keyless_fallback must be true")
        if web.get("keyless_rescue") is not True:
            fail("inception web.keyless_rescue must be true")
        plugins_enabled = (config.get("plugins") or {}).get("enabled") or []
        if plugins_enabled != ["inception"]:
            fail("inception plugins.enabled must be [inception]")
    skills = agent_dir / "skills"
    required_by_skill = {
        "author-profile": [
            "docs_resolve",
            "docs_ask",
            "probe_knob",
            "scaffold_profile",
            "check_profile",
        ],
        "probe-knob": ["docs_resolve", "docs_ask", "probe_knob"],
        "review-profile": ["check_profile"],
    }
    for skill_name, needed_tools in required_by_skill.items():
        skill_md = skills / skill_name / "SKILL.md"
        if not skill_md.is_file():
            continue
        body = skill_md.read_text(encoding="utf-8")
        if "mcp_*" not in body:
            fail(f"{skill_md.relative_to(ROOT)} must tell the model not to call raw mcp_* tools")
        if skill_name == "author-profile":
            if "Step 0" not in body or "Step 5" not in body:
                fail(f"{skill_md.relative_to(ROOT)} must map playbook steps 0-4 then 5-10")
        if skill_name == "review-profile" and "What is in context on turn 40" not in body:
            fail(f"{skill_md.relative_to(ROOT)} must walk the §10 heuristics")
        front_end = body.find("\n---", 3)
        front = yaml.safe_load(body[4:front_end]) if front_end > 0 else {}
        hermes = ((front or {}).get("metadata") or {}).get("hermes") or {}
        tool_names = [str(item) for item in (hermes.get("requires_tools") or [])]
        for needed in needed_tools:
            if needed not in tool_names:
                fail(
                    f"{skill_md.relative_to(ROOT)} requires_tools must include {needed!r}"
                )


def _check_literature_sweep_env(skill_md: Path, front: dict, hermes: dict) -> None:
    if hermes.get("required_environment_variables") is not None:
        fail(
            f"{skill_md.relative_to(ROOT)} must not nest "
            "required_environment_variables under metadata.hermes"
        )
    env_list = front.get("required_environment_variables")
    if not isinstance(env_list, list) or not env_list:
        fail(
            f"{skill_md.relative_to(ROOT)} must declare top-level "
            "required_environment_variables as official objects"
        )
        return
    names: set[str] = set()
    for item in env_list:
        if not isinstance(item, dict) or not item.get("name"):
            fail(
                f"{skill_md.relative_to(ROOT)} each env entry must be an "
                "object with name, prompt, help, required_for"
            )
            continue
        names.add(str(item["name"]))
        for key in ("prompt", "help", "required_for"):
            if not item.get(key):
                fail(
                    f"{skill_md.relative_to(ROOT)} {item['name']} missing {key}"
                )
    if "CONTEXT7_API_KEY" in names:
        fail(
            f"{skill_md.relative_to(ROOT)} must not declare CONTEXT7_API_KEY"
        )
    for needed in ("CROSSREF_MAILTO", "UNPAYWALL_EMAIL"):
        if needed not in names:
            fail(
                f"{skill_md.relative_to(ROOT)} required_environment_variables "
                f"must include {needed}"
            )


def _check_hdr_script_twins(agent_dir: Path) -> None:
    if agent_dir.name != "research-bot":
        return
    twins = (
        ("plugins/hdr/scripts/dedupe_urls.py", "skills/source-triage/scripts/dedupe_urls.py"),
        ("plugins/hdr/scripts/crossref.py", "skills/literature-sweep/scripts/crossref.py"),
        ("plugins/hdr/scripts/unpaywall.py", "skills/literature-sweep/scripts/unpaywall.py"),
        ("plugins/hdr/scripts/pdf_text.py", "skills/literature-sweep/scripts/pdf_text.py"),
    )
    for plugin_rel, skill_rel in twins:
        plugin_path = agent_dir / Path(plugin_rel)
        skill_path = agent_dir / Path(skill_rel)
        if not plugin_path.is_file() or not skill_path.is_file():
            fail(
                f"{agent_dir.name} missing script twin "
                f"{plugin_rel} / {skill_rel}"
            )
            continue
        if plugin_path.read_bytes() != skill_path.read_bytes():
            fail(
                f"{agent_dir.name} script drift: {plugin_rel} != {skill_rel}. "
                "Keep the copies byte-identical or delete one home."
            )


def main() -> int:
    agents_root = ROOT / "agents"
    if not agents_root.is_dir():
        fail("missing agents/")
        return 1
    check_product_name()
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
