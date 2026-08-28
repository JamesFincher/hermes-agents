"""Unit tests for the inception plugin. No live Hermes. No API keys."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "agents" / "inception" / "plugins" / "inception"
PKG_NAME = "inception_plugin"


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
        raise RuntimeError("unable to load inception plugin package")
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
    def __init__(self) -> None:
        self.state = FakeState()
        self.tools: list[tuple[str, str]] = []
        self.hooks: list[str] = []
        self.sections: list[str] = []
        self.mcp_calls: list[tuple[str, str, dict[str, Any]]] = []
        self.mcp_response: Any = {"ok": True, "result": {"id": "lib"}}

    def get_config(self, key: str, default: Any = None) -> Any:
        return default

    def plugin_data_dir(self, plugin_id: str) -> Path:
        home = Path(os.environ["HERMES_HOME"])
        path = home / "plugin-data" / plugin_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def register_tool(self, **kwargs: Any) -> None:
        self.tools.append((str(kwargs.get("name")), str(kwargs.get("toolset"))))

    def register_hook(self, name: str, _handler: Any) -> None:
        self.hooks.append(name)

    def register_system_prompt_section(self, name: str, *_args: Any, **_kwargs: Any) -> None:
        self.sections.append(name)

    def call_mcp(self, server: str, tool: str, arguments: dict[str, Any], **_kwargs: Any) -> Any:
        self.mcp_calls.append((server, tool, arguments))
        if isinstance(self.mcp_response, Exception):
            raise self.mcp_response
        return self.mcp_response


class InceptionPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self._home = tempfile.TemporaryDirectory()
        os.environ["HERMES_HOME"] = self._home.name
        os.environ.pop("INCEPTION_LIBRARY_ROOT", None)
        self.pkg = _load_plugin_package()
        self.ctx = FakeCtx()
        self.pkg.register(self.ctx)

    def tearDown(self) -> None:
        self._home.cleanup()
        os.environ.pop("HERMES_HOME", None)
        os.environ.pop("INCEPTION_LIBRARY_ROOT", None)

    def test_register_tools_and_hooks(self) -> None:
        names = {name for name, toolset in self.ctx.tools}
        self.assertEqual(
            names,
            {
                "docs_resolve",
                "docs_ask",
                "probe_knob",
                "scaffold_profile",
                "check_profile",
            },
        )
        self.assertTrue(all(toolset == "inception" for _, toolset in self.ctx.tools))
        self.assertIn("pre_tool_call", self.ctx.hooks)
        self.assertIn("transform_tool_result", self.ctx.hooks)
        self.assertIn("inception.factory-contract", self.ctx.sections)

    def test_probe_doc_and_unv_gate(self) -> None:
        probe = self.pkg.tools.probe_knob
        ok = json.loads(
            probe(
                {
                    "knob": "memory.provider",
                    "decision": "accept",
                    "tag": "DOC",
                    "url": "https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin",
                    "reason": "Official provider id.",
                    "code_depends": True,
                }
            )
        )
        self.assertTrue(ok["ok"])
        blocked = json.loads(
            probe(
                {
                    "knob": "plugins.doctor",
                    "decision": "reject",
                    "tag": "UNV",
                    "reason": "No official doctor action.",
                    "code_depends": True,
                }
            )
        )
        self.assertIn("error", blocked)

    def test_docs_without_url_stores_no_card(self) -> None:
        self.ctx.mcp_response = {"ok": True, "result": "no link here"}
        payload = json.loads(
            self.pkg.tools.docs_resolve(
                {"query": "custom_toolsets", "library_name": "Hermes Agent"}
            )
        )
        self.assertFalse(payload["stored"])
        self.assertIsNone(payload["openable_url"])
        store = self.pkg.store.load_store()
        self.assertEqual(store["cards"], [])

    def test_docs_with_url_stores_card(self) -> None:
        self.ctx.mcp_response = {
            "ok": True,
            "result": "See https://hermes-agent.nousresearch.com/docs/user-guide/configuration",
        }
        payload = json.loads(
            self.pkg.tools.docs_ask(
                {
                    "library_id": "/nousresearch/hermes-agent",
                    "query": "compression.in_place",
                }
            )
        )
        self.assertTrue(payload["stored"])
        self.assertTrue(str(payload["openable_url"]).startswith("https://"))

    def test_docs_down_degrades(self) -> None:
        fixture = json.loads(
            (ROOT / "agents/inception/evals/fixtures/context7_down.json").read_text(
                encoding="utf-8"
            )
        )
        self.ctx.mcp_response = fixture
        payload = json.loads(
            self.pkg.tools.docs_ask(
                {"library_id": "/nousresearch/hermes-agent", "query": "hooks"}
            )
        )
        self.assertIn("error", payload)
        self.assertFalse(payload.get("stored"))

    def test_handlers_never_raise(self) -> None:
        for handler in (
            self.pkg.tools.docs_resolve,
            self.pkg.tools.docs_ask,
            self.pkg.tools.probe_knob,
            self.pkg.tools.scaffold_profile,
            self.pkg.tools.check_profile,
        ):
            result = json.loads(handler(None))
            self.assertIn("error", result)

    def _library_root(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "docs").mkdir()
        (tmp / "scripts").mkdir()
        shutil.copy(ROOT / "docs" / "PROFILE-PLAYBOOK.md", tmp / "docs" / "PROFILE-PLAYBOOK.md")
        shutil.copy(ROOT / "scripts" / "validate_factory.py", tmp / "scripts" / "validate_factory.py")
        os.environ["INCEPTION_LIBRARY_ROOT"] = str(tmp)
        return tmp

    def test_scaffold_and_check(self) -> None:
        library = self._library_root()
        self.addCleanup(lambda: shutil.rmtree(library, ignore_errors=True))
        built = json.loads(
            self.pkg.tools.scaffold_profile(
                {
                    "name": "shelf-note",
                    "job": "Files meeting notes. Does not write product apps.",
                }
            )
        )
        self.assertTrue(built.get("ok"), built)
        dest = Path(built["path"])
        self.assertTrue((dest / "SOUL.md").is_file())
        self.assertTrue((dest / "HONEST-LIMITS.md").is_file())
        self.assertFalse((dest / "plugins").exists())
        checked = json.loads(self.pkg.tools.check_profile({"path": str(dest)}))
        self.assertTrue(checked.get("ok"), checked)

    def test_scaffold_reserved_and_forbidden(self) -> None:
        library = self._library_root()
        self.addCleanup(lambda: shutil.rmtree(library, ignore_errors=True))
        reserved = json.loads(
            self.pkg.tools.scaffold_profile({"name": "hermes", "job": "no"})
        )
        self.assertIn("error", reserved)
        ouro = json.loads(self.pkg.tools.scaffold_profile({"name": "forge", "job": "no"}))
        self.assertIn("error", ouro)
        foreign = json.loads(
            self.pkg.tools.scaffold_profile({"name": "research-bot", "job": "no"})
        )
        self.assertIn("error", foreign)

    def test_fence_blocks_reserved_name(self) -> None:
        blocked = self.pkg.hooks.pre_tool_call(
            "scaffold_profile", {"name": "hermes", "job": "no"}
        )
        self.assertEqual(blocked["action"], "block")

    def test_fence_fail_closed(self) -> None:
        original = self.pkg.store.ledger.load_store

        def boom() -> Any:
            raise RuntimeError("store down")

        self.pkg.store.ledger.load_store = boom  # type: ignore[method-assign]
        try:
            blocked = self.pkg.hooks.pre_tool_call("scaffold_profile", {"name": "ok"})
        finally:
            self.pkg.store.ledger.load_store = original  # type: ignore[method-assign]
        self.assertEqual(blocked["action"], "block")
        self.assertIn("could not evaluate", blocked["message"])

    def test_distill_fail_open(self) -> None:
        self.assertIsNone(self.pkg.hooks.transform_tool_result(object()))

    def test_digest_cap(self) -> None:
        for index in range(30):
            self.pkg.store.add_probe(
                {
                    "knob": f"k{index}",
                    "decision": "default",
                    "tag": "INF",
                    "reason": "x" * 40,
                }
            )
        result = self.pkg.hooks.pre_llm_call()
        text = result["context"]
        self.assertLessEqual(len(text), 800)

    def test_footer_appends(self) -> None:
        out = self.pkg.hooks.transform_llm_output("hello")
        self.assertIn("Factory run", out)

    def test_migration_idempotent(self) -> None:
        path = self.pkg.store.ledger.store_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"probes": [{"knob": "a"}]}), encoding="utf-8")
        first = self.pkg.store.migrate(json.loads(path.read_text(encoding="utf-8")))
        second = self.pkg.store.migrate(first)
        self.assertEqual(first["version"], 1)
        self.assertEqual(second["version"], 1)
        self.assertEqual(first["probes"][0]["knob"], "a")

    def test_concurrent_writes(self) -> None:
        errors: list[str] = []

        def worker(index: int) -> None:
            try:
                self.pkg.store.add_probe(
                    {
                        "knob": f"k{index}",
                        "decision": "default",
                        "tag": "INF",
                        "reason": "concurrent",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        store = self.pkg.store.load_store()
        self.assertEqual(len(store["probes"]), 8)

    def test_governor_hard_blocks_scaffold(self) -> None:
        for _ in range(81):
            self.pkg.hooks.pre_api_request({"approx_input_tokens": 10})
        blocked = self.pkg.hooks.pre_tool_call(
            "scaffold_profile", {"name": "ok-name", "job": "x"}
        )
        self.assertEqual(blocked["action"], "block")

    def test_inception_config_does_not_enable_hdr(self) -> None:
        text = (ROOT / "agents" / "inception" / "config.yaml").read_text(encoding="utf-8")
        self.assertNotIn("\n    - hdr\n", text)
        self.assertIn("inception", text)

    def test_eval_tasks_shape(self) -> None:
        rows = []
        for line in (ROOT / "agents/inception/evals/tasks.jsonl").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.strip():
                rows.append(json.loads(line))
        self.assertGreaterEqual(len(rows), 8)
        self.assertGreaterEqual(sum(1 for row in rows if row.get("adversarial")), 2)

    def test_reserved_name_script(self) -> None:
        script = ROOT / "agents/inception/skills/author-profile/scripts/reserved_names.py"
        spec = importlib.util.spec_from_file_location("reserved_names", script)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.main(["reserved_names.py", "hermes"]), 1)
        self.assertEqual(mod.main(["reserved_names.py", "ok-agent"]), 0)


if __name__ == "__main__":
    unittest.main()
