"""Unit tests for army-runtime. No live Hermes."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "army-runtime"
PKG_NAME = "army_runtime_plugin"


def _load_plugin_package() -> ModuleType:
    existing = sys.modules.get(PKG_NAME)
    if existing is not None and getattr(existing, "__file__", None) == str(
        PLUGIN_DIR / "__init__.py"
    ):
        return existing
    for key in list(sys.modules):
        if key == PKG_NAME or key.startswith(f"{PKG_NAME}."):
            del sys.modules[key]
    spec = importlib.util.spec_from_file_location(
        PKG_NAME,
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load army-runtime plugin package")
    pkg = importlib.util.module_from_spec(spec)
    pkg.__path__ = [str(PLUGIN_DIR)]
    sys.modules[PKG_NAME] = pkg
    spec.loader.exec_module(pkg)
    return pkg


class FakeState:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value


class FakeCtx:
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or {}
        self.state = FakeState()
        self.tools: list[tuple[str, str]] = []
        self.hooks: list[str] = []
        self.middleware: list[str] = []

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def register_tool(self, **kwargs: Any) -> None:
        self.tools.append((str(kwargs.get("name")), str(kwargs.get("toolset"))))

    def register_hook(self, name: str, _handler: Any) -> None:
        self.hooks.append(name)

    def register_middleware(self, name: str, _handler: Any) -> None:
        self.middleware.append(name)


class PluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self._prev_hermes = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        self.addCleanup(self._restore_hermes)
        self.pkg = _load_plugin_package()
        self.runtime = sys.modules[f"{PKG_NAME}.runtime"]
        self.ledger = sys.modules[f"{PKG_NAME}.ledger"]
        self.policy = sys.modules[f"{PKG_NAME}.policy"]
        self.tools = sys.modules[f"{PKG_NAME}.tools"]
        self.hooks = sys.modules[f"{PKG_NAME}.hooks"]
        self.middleware = sys.modules[f"{PKG_NAME}.middleware"]
        self.ctx = FakeCtx({"citation_style": "apa", "write_policy": "research"})
        self.runtime.set_ctx(self.ctx)

    def _restore_hermes(self) -> None:
        if self._prev_hermes is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._prev_hermes

    def test_plugin_data_is_under_hermes_home_not_install_tree(self) -> None:
        root = self.runtime.plugin_data_root()
        self.assertEqual(root, self.home / "plugin-data" / "army-runtime")
        self.assertFalse(str(root).startswith(str(PLUGIN_DIR)))

    def test_ledger_add_list_cite_dedupe(self) -> None:
        self.ledger.init_ledger()
        first = self.ledger.add_source(
            url="https://example.com/docs",
            title="Example Docs",
            quote="cited knobs only",
            kind="docs",
        )
        second = self.ledger.add_source(
            url="https://example.com/docs",
            title="Example Docs",
            kind="docs",
        )
        self.assertTrue(first.get("ok"))
        self.assertTrue(second.get("updated"))
        listed = self.ledger.list_sources()
        self.assertEqual(listed["count"], 1)
        cited = self.ledger.cite_sources(None, "apa")
        self.assertEqual(cited["count"], 1)
        self.assertIn("https://example.com/docs", cited["citations"][0]["text"])

    def test_claim_check_unsourced(self) -> None:
        self.ledger.init_ledger()
        result = self.ledger.check_claim("The flux capacitor is documented at 1.21 GW.")
        self.assertTrue(result.get("ok"))
        self.assertFalse(result.get("supported"))

    def test_harvest_from_web_search(self) -> None:
        self.ledger.init_ledger()
        payload = json.dumps(
            {
                "results": [
                    {
                        "url": "https://hermes-agent.nousresearch.com/docs",
                        "title": "Hermes docs",
                        "snippet": "Profile distributions carry plugins.",
                    }
                ]
            }
        )
        harvested = self.ledger.harvest_from_tool("web_search", {}, payload)
        self.assertGreaterEqual(harvested["harvested"], 1)
        listed = self.ledger.list_sources("hermes")
        self.assertEqual(listed["count"], 1)

    def test_write_policy_gated_by_setting(self) -> None:
        blocked = self.policy.write_policy(
            "write_file", {"path": "src/app.py", "content": "print(1)"}
        )
        self.assertEqual((blocked or {}).get("action"), "block")
        self.runtime.set_ctx(FakeCtx({"write_policy": "off"}))
        allowed = self.policy.write_policy(
            "write_file", {"path": "src/app.py", "content": "print(1)"}
        )
        self.assertIsNone(allowed)
        self.runtime.set_ctx(self.ctx)
        allowed_artifact = self.policy.write_policy(
            "write_file", {"path": "notes/findings.md", "content": "ok"}
        )
        self.assertIsNone(allowed_artifact)

    def test_hooks_contract_does_not_dump_skills(self) -> None:
        self.hooks.on_session_start("s1", "model", "cli")
        self.assertTrue(
            (self.home / "plugin-data" / "army-runtime" / "source-ledger.json").is_file()
        )
        injected = self.hooks.pre_llm_call("s1", "What does the spec say?")
        self.assertIsInstance(injected, dict)
        assert injected is not None
        self.assertIn("source_ledger_cite", injected["context"])
        self.assertNotIn("SKILL.md", injected["context"])
        self.assertNotIn("available_skills", injected["context"])
        blocked = self.hooks.pre_tool_call(
            "write_file", {"path": "pkg/main.ts"}, "task"
        )
        self.assertEqual((blocked or {}).get("action"), "block")

    def test_tools_return_json_and_never_raise(self) -> None:
        self.ledger.init_ledger()
        added = json.loads(
            self.tools.source_ledger_add(
                {"url": "https://a.example/x", "title": "A", "quote": "q"}
            )
        )
        self.assertTrue(added.get("ok"))
        missing = json.loads(self.tools.source_ledger_add({}))
        self.assertIn("error", missing)
        cited = json.loads(self.tools.source_ledger_cite({}))
        self.assertTrue(cited.get("ok"))

    def test_middleware_defaults_style(self) -> None:
        filled = self.middleware.tool_request_defaults(
            tool_name="source_ledger_cite", args={"ids": [1]}
        )
        self.assertIsNotNone(filled)
        assert filled is not None
        self.assertEqual(filled["args"]["style"], "apa")
        self.assertEqual(filled["source"], "army-runtime")

    def test_register_uses_army_toolset(self) -> None:
        ctx = FakeCtx()
        self.pkg.register(ctx)
        names = [name for name, _toolset in ctx.tools]
        toolsets = {toolset for _name, toolset in ctx.tools}
        self.assertEqual(
            names,
            [
                "source_ledger_add",
                "source_ledger_list",
                "source_ledger_cite",
                "source_ledger_check",
            ],
        )
        self.assertEqual(toolsets, {"army"})
        self.assertEqual(
            ctx.hooks,
            ["on_session_start", "pre_llm_call", "pre_tool_call", "post_tool_call"],
        )
        self.assertEqual(ctx.middleware, ["tool_request"])
        self.assertNotIn("register_skill", dir(ctx))


if __name__ == "__main__":
    unittest.main()
