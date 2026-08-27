"""Unit tests for the research-bot profile plugin. No live Hermes."""

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
PLUGIN_DIR = ROOT / "agents" / "research-bot" / "plugins" / "research-bot"
PKG_NAME = "research_bot_plugin"


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
        raise RuntimeError("unable to load research-bot plugin package")
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
        self.mcp_calls: list[tuple[str, str, dict[str, Any]]] = []
        self.mcp_responses: dict[str, Any] = {}

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def plugin_data_dir(self, plugin_id: str) -> Path:
        home = Path(os.environ["HERMES_HOME"])
        path = home / "plugin-data" / plugin_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def register_tool(self, **kwargs: Any) -> None:
        self.tools.append((str(kwargs.get("name")), str(kwargs.get("toolset"))))

    def register_hook(self, name: str, _handler: Any) -> None:
        self.hooks.append(name)

    def call_mcp(self, server: str, tool: str, arguments: dict[str, Any] | None = None) -> Any:
        payload = arguments or {}
        self.mcp_calls.append((server, tool, payload))
        canned = self.mcp_responses.get(tool)
        if canned is not None:
            return canned
        return {"ok": True, "result": f"{server}:{tool}:{payload.get('query', '')}"}


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
        self.ctx = FakeCtx({"citation_style": "apa"})
        self.runtime.set_ctx(self.ctx)

    def _restore_hermes(self) -> None:
        if self._prev_hermes is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._prev_hermes

    def test_register_uses_this_profile_toolset(self) -> None:
        self.pkg.register(self.ctx)
        names = {name for name, _toolset in self.ctx.tools}
        toolsets = {toolset for _name, toolset in self.ctx.tools}
        self.assertEqual(
            names,
            {
                "resolve_library",
                "docs_query",
                "source_ledger_add",
                "source_ledger_list",
                "cite_source",
                "source_ledger_check",
            },
        )
        self.assertEqual(toolsets, {"research-bot"})
        self.assertEqual(
            set(self.ctx.hooks),
            {"on_session_start", "pre_llm_call", "pre_tool_call", "post_tool_call"},
        )

    def test_plugin_data_is_under_hermes_home_not_install_tree(self) -> None:
        root = self.runtime.plugin_data_root()
        self.assertEqual(root, self.home / "plugin-data" / "research-bot")
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

    def test_resolve_library_calls_mcp_then_ledgers(self) -> None:
        self.ledger.init_ledger()
        self.ctx.mcp_responses["resolve-library-id"] = {
            "ok": True,
            "result": "/nousresearch/hermes-agent",
        }
        payload = json.loads(self.tools.resolve_library({"query": "hermes-agent"}))
        self.assertTrue(payload.get("ok"))
        self.assertEqual(
            self.ctx.mcp_calls,
            [("context7", "resolve-library-id", {"query": "hermes-agent"})],
        )
        listed = self.ledger.list_sources()
        self.assertEqual(listed["count"], 1)
        self.assertIn("context7://resolve-library-id", listed["sources"][0]["url"])

    def test_docs_query_calls_unsanitized_mcp_name(self) -> None:
        self.ledger.init_ledger()
        self.ctx.mcp_responses["query-docs"] = {"ok": True, "result": "Profiles are homes."}
        payload = json.loads(
            self.tools.docs_query(
                {"library_id": "/nousresearch/hermes-agent", "query": "profiles"}
            )
        )
        self.assertTrue(payload.get("ok"))
        self.assertEqual(self.ctx.mcp_calls[0][0], "context7")
        self.assertEqual(self.ctx.mcp_calls[0][1], "query-docs")
        self.assertEqual(
            self.ctx.mcp_calls[0][2]["libraryId"], "/nousresearch/hermes-agent"
        )

    def test_write_policy_blocks_product_code_allows_notes(self) -> None:
        blocked = self.policy.write_policy(
            "write_file", {"path": "src/app.py", "content": "print(1)"}
        )
        self.assertEqual((blocked or {}).get("action"), "block")
        allowed_artifact = self.policy.write_policy(
            "write_file", {"path": "notes/findings.md", "content": "ok"}
        )
        self.assertIsNone(allowed_artifact)
        scaffold = self.policy.write_policy(
            "terminal", {"command": "npm init -y"}
        )
        self.assertEqual((scaffold or {}).get("action"), "block")

    def test_hooks_contract_does_not_dump_skills_or_harvest_mcp_names(self) -> None:
        self.hooks.on_session_start("s1", "model", "cli")
        self.assertTrue(
            (self.home / "plugin-data" / "research-bot" / "source-ledger.json").is_file()
        )
        injected = self.hooks.pre_llm_call("s1", "What does the spec say?")
        self.assertIsInstance(injected, dict)
        assert injected is not None
        self.assertIn("cite_source", injected["context"])
        self.assertIn("resolve_library", injected["context"])
        self.assertNotIn("SKILL.md", injected["context"])
        self.assertNotIn("available_skills", injected["context"])
        blocked = self.hooks.pre_tool_call(
            "write_file", {"path": "pkg/main.ts"}, "task"
        )
        self.assertEqual((blocked or {}).get("action"), "block")
        before = self.ledger.list_sources()["count"]
        self.hooks.post_tool_call("mcp_context7_query_docs", {"query": "x"}, "hit", "t")
        self.assertEqual(self.ledger.list_sources()["count"], before)

    def test_ledger_survives_child_session_lineage(self) -> None:
        self.runtime.set_ctx(self.ctx)
        path = self.ledger.ledger_path()
        self.assertEqual(path, self.home / "plugin-data" / "research-bot" / "source-ledger.json")
        self.assertNotIn("s1", str(path))
        self.assertNotIn("session", path.name)

    def test_does_not_hook_police_intercepted_agent_tools(self) -> None:
        for name in ("todo", "memory", "session_search", "delegate_task"):
            self.assertIsNone(
                self.hooks.pre_tool_call(name, {"text": "x"}, "task"),
                msg=name,
            )

    def test_pre_llm_call_is_user_message_contract_not_cached_soul(self) -> None:
        self.hooks.on_session_start("s1", "model", "cli")
        injected = self.hooks.pre_llm_call("s1", "Cite the spec.")
        assert injected is not None
        self.assertIn("RESEARCH CONTRACT", injected["context"])
        self.assertIn("LEDGER:", injected["context"])
        self.assertIn("MEMORY.md personality", injected["context"])
        self.assertLessEqual(len(injected["context"]), 10000)

    def test_schemas_are_flat_and_say_when_to_call(self) -> None:
        schemas = sys.modules[f"{PKG_NAME}.schemas"]
        for schema in (
            schemas.RESOLVE_LIBRARY,
            schemas.DOCS_QUERY,
            schemas.CITE_SOURCE,
        ):
            self.assertNotIn("function", schema)
            self.assertIn("name", schema)
            self.assertIn("parameters", schema)
            self.assertEqual(schema["parameters"]["type"], "object")
            self.assertIn("When to call", schema["description"])
        self.assertEqual(schemas.CITE_SOURCE["name"], "cite_source")
        self.assertIn("cite_source", schemas.CITE_SOURCE["description"])

    def test_handlers_return_json_string_not_dict(self) -> None:
        self.ledger.init_ledger()
        raw = self.tools.source_ledger_add(
            {"url": "https://b.example/y"}, task_id="task-1"
        )
        self.assertIsInstance(raw, str)
        payload = json.loads(raw)
        self.assertTrue(payload.get("ok"))
        missing = self.tools.resolve_library({}, task_id="task-1")
        self.assertIsInstance(missing, str)
        self.assertIn("error", json.loads(missing))

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
        cited = json.loads(self.tools.cite_source({}))
        self.assertTrue(cited.get("ok"))
        empty_resolve = json.loads(self.tools.resolve_library({}))
        self.assertIn("error", empty_resolve)


if __name__ == "__main__":
    unittest.main()
