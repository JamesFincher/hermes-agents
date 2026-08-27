"""Unit tests for the HDR plugin. No live Hermes. No API keys."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "agents" / "research-bot" / "plugins" / "hdr"
PKG_NAME = "hdr_plugin"


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
        raise RuntimeError("unable to load hdr plugin package")
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
        self.sections: list[tuple[str, str]] = []
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

    def register_system_prompt_section(self, name: str, content: str, position: str = "") -> None:
        del position
        self.sections.append((name, content))

    def call_mcp(self, server: str, tool: str, arguments: dict[str, Any] | None = None) -> Any:
        payload = arguments or {}
        self.mcp_calls.append((server, tool, payload))
        key = f"{server}:{tool}"
        if key in self.mcp_responses:
            return self.mcp_responses[key]
        return {"ok": True, "result": {"docsUrl": "https://example.com/docs", "query": payload}}


class HdrTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["HERMES_HOME"] = self._tmp.name
        self.pkg = _load_plugin_package()
        self.ctx = FakeCtx()
        self.pkg.register(self.ctx)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_register_surfaces(self) -> None:
        names = {name for name, toolset in self.ctx.tools}
        self.assertIn("research_plan", names)
        self.assertIn("claim_verify", names)
        self.assertIn("resolve_library", names)
        self.assertTrue(all(toolset == "hdr" for _, toolset in self.ctx.tools))
        self.assertNotIn("source_ledger_check", names)
        self.assertIn("pre_tool_call", self.ctx.hooks)
        self.assertIn("on_session_reset", self.ctx.hooks)
        self.assertIn("transform_tool_result", self.ctx.hooks)
        self.assertEqual({name for name, _ in self.ctx.sections}, {"hdr.method", "hdr.effort", "hdr.integrity"})
        total = sum(len(text) for _, text in self.ctx.sections)
        self.assertLessEqual(total, 8000)
        for _, text in self.ctx.sections:
            self.assertLessEqual(len(text), 4000)

    def test_migration_idempotent(self) -> None:
        ledger = self.pkg.store.ledger
        path = ledger.ledger_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": [
                        {
                            "id": 1,
                            "url": "https://example.com/a?utm_source=x",
                            "title": "Old",
                            "quote": "hello",
                            "kind": "web",
                            "retrieved": "2026-01-01T00:00:00+00:00",
                            "origin": "manual",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        first = ledger.load_ledger()
        self.assertEqual(first["version"], 2)
        self.assertEqual(first["sources"][0]["id"], "S1")
        self.assertEqual(first["sources"][0]["tier"], "D")
        self.assertTrue(first["sources"][0]["needs_backfill"])
        second = ledger.load_ledger()
        self.assertEqual(first["sources"][0]["id"], second["sources"][0]["id"])
        self.assertEqual(len(second["sources"]), 1)

    def test_eight_thread_writes(self) -> None:
        errors: list[str] = []

        def writer(index: int) -> None:
            try:
                result = self.pkg.store.ledger.add_source(
                    {
                        "url": f"https://example.com/page-{index}",
                        "title": f"Page {index}",
                        "quote": f"quote {index}",
                    }
                )
                if result.get("error"):
                    errors.append(str(result))
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        sources = self.pkg.store.ledger.list_sources()
        self.assertEqual(len(sources), 8)
        ids = {src["id"] for src in sources}
        self.assertEqual(len(ids), 8)

    def test_evidence_bus_card_and_byte_exact(self) -> None:
        page = ("The saturation rule is computed by gap_scan. " * 1000) + "END-MARKER-4040"
        self.assertGreater(len(page), 40000)
        card = self.pkg.hooks.transform_tool_result(
            "web_extract",
            {"url": "https://example.com/long", "text": page},
            {"url": "https://example.com/long"},
        )
        self.assertIsInstance(card, str)
        payload = json.loads(card)
        self.assertTrue(payload.get("card"))
        tokens = max(1, (len(card) + 3) // 4)
        self.assertLessEqual(tokens, 400)
        digest = payload["full"].split("/")[-1].split(" ")[0].replace(".txt", "")
        stored = self.pkg.store.bus.read_corpus(digest, offset=0, limit=len(page) + 10)
        self.assertEqual(stored["text"], page)

        class Boom:
            def __str__(self) -> str:
                raise RuntimeError("boom")

        self.assertIsNone(self.pkg.hooks.transform_tool_result("web_extract", Boom()))

    def test_dedupe_and_citation_gate(self) -> None:
        page = "Primary finding: the widget shipped in 2024 with 12% growth."
        self.pkg.hooks.transform_tool_result(
            "web_extract",
            {"url": "https://example.com/a?utm_source=x", "text": page},
            {"url": "https://example.com/a?utm_source=x"},
        )
        blocked = self.pkg.hooks.pre_tool_call(
            "web_extract",
            {"url": "https://example.com/a"},
        )
        self.assertEqual((blocked or {}).get("action"), "block")
        self.assertIn("Already retrieved", (blocked or {}).get("message", ""))
        refused = self.pkg.hooks.pre_tool_call(
            "write_file",
            {"path": "briefs/out.md", "content": "Growth was 12% [S99]."},
        )
        self.assertEqual((refused or {}).get("action"), "block")
        self.assertIn("S99", (refused or {}).get("message", ""))

    def test_write_allowlist(self) -> None:
        blocked = self.pkg.hooks.pre_tool_call(
            "write_file",
            {"path": "src/app.py", "content": "print(1)\n"},
        )
        self.assertEqual((blocked or {}).get("action"), "block")
        allowed_check = self.pkg.hooks.pre_tool_call(
            "write_file",
            {"path": "notes/scratch.py", "content": "print(1)\n"},
        )
        self.assertIsNone(allowed_check)

    def test_plan_digest_and_gap_scan(self) -> None:
        plan = json.loads(
            self.pkg.tools.research_plan(
                {
                    "action": "create",
                    "question": "What shipped in 2024?",
                    "tier": "standard",
                    "open_questions": ["What shipped in 2024?"],
                }
            )
        )
        self.assertTrue(plan.get("ok"))
        self.assertEqual(plan["budget"]["tokens"], 200000)
        digest = self.pkg.hooks.pre_llm_call("s", "hello")
        self.assertIsNotNone(digest)
        self.assertLessEqual(len((digest or {}).get("context", "")), 1200)
        self.pkg.store.ledger.add_source(
            {
                "url": "https://arxiv.org/abs/2401.00001",
                "title": "What shipped in 2024?",
                "tier": "A",
                "kind": "primary",
                "run_id": plan["run_id"],
            }
        )
        scan = json.loads(self.pkg.tools.gap_scan({"detail": "summary"}))
        self.assertTrue(scan.get("ok"))
        self.assertIn("saturation", scan)
        self.assertIsInstance(scan["saturation"], float)

    def test_three_worker_batch_parent_stays_small(self) -> None:
        mandates = ["Mandate A", "Mandate B", "Mandate C"]
        self.pkg.tools.research_plan(
            {
                "question": "Compare three entities",
                "open_questions": mandates,
                "tier": "standard",
            }
        )
        parent_blobs: list[str] = []
        live = Path(os.environ["HERMES_HOME"]) / "cache" / "delegation" / "live" / "batch-1"
        live.mkdir(parents=True, exist_ok=True)
        for index, mandate in enumerate(mandates, start=1):
            brief = json.loads(
                self.pkg.tools.worker_brief(
                    {
                        "open_question": mandate,
                        "boundary": "Do not cover the other mandates",
                    }
                )
            )
            parent_blobs.append(brief["brief"])
            page = f"<html>secret page body for {mandate} " + ("RAW" * 200) + "</html>"
            log = live / f"task-{index}.log"
            log.write_text(
                f"FINDING: short note for {mandate}\nCARDS: S{index}\nhttps://example.com/w{index}\n",
                encoding="utf-8",
            )
            harvest = json.loads(
                self.pkg.tools.worker_harvest(
                    {"subagent_id": f"sa-{index}", "transcript_path": str(log)}
                )
            )
            parent_blobs.append(json.dumps(harvest))
            self.assertNotIn("RAW", json.dumps(harvest))
            self.assertNotIn(page, json.dumps(harvest))
        parent_text = "\n".join(parent_blobs)
        tokens = max(1, (len(parent_text) + 3) // 4)
        self.assertLess(tokens, 4000)
        self.assertNotIn("secret page body", parent_text)

    def test_claim_verify_and_conflicts(self) -> None:
        text = "The device reached 12% efficiency in 2024 at NIST."
        self.pkg.hooks.transform_tool_result(
            "web_extract",
            {"url": "https://www.nist.gov/note", "text": text},
            {"url": "https://www.nist.gov/note"},
        )
        verify = json.loads(self.pkg.tools.claim_verify({"claim": text}))
        self.assertEqual(verify["status"], "supported")
        self.pkg.store.claims.upsert_claim(
            "efficiency", src="S1", stance="supports", conf=0.9
        )
        self.pkg.store.claims.upsert_claim(
            "efficiency", src="S2", stance="contradicts", conf=0.8
        )
        report = json.loads(self.pkg.tools.conflict_report({}))
        self.assertGreaterEqual(report["count"], 1)
        cite = json.loads(self.pkg.tools.cite_source({}))
        self.assertGreaterEqual(cite["count"], 1)
        out = self.pkg.hooks.transform_llm_output("The device reached 12% efficiency [S1].")
        self.assertIsNotNone(out)
        self.assertIn("## Sources", out or "")

    def test_governor_forced_overspend(self) -> None:
        created = json.loads(
            self.pkg.tools.research_plan({"question": "overspend", "tier": "quick"})
        )
        self.assertTrue(created.get("ok"))
        current = self.pkg.store.run.load_run()
        assert current is not None
        current["spend"]["tokens"] = current["budget"]["tokens"] + 10
        current["governor"] = self.pkg.store.run.governor_state(current)
        self.pkg.store.run.save_run(current)
        self.assertEqual(current["governor"], "HARD")
        blocked = self.pkg.hooks.pre_tool_call("web_extract", {"url": "https://example.com/z"})
        self.assertEqual((blocked or {}).get("action"), "block")
        self.pkg.store.ledger.add_source(
            {
                "url": "https://example.com/prior",
                "title": "Prior",
                "quote": "supported finding",
                "run_id": created["run_id"],
            }
        )
        search = json.loads(self.pkg.tools.evidence_search({}))
        self.assertGreaterEqual(search["count"], 1)
        drafted = self.pkg.store.draft.draft_brief()
        self.assertTrue(drafted.get("brief"))
        self.assertIn("[S1]", drafted["brief"])
        write = self.pkg.hooks.pre_tool_call(
            "write_file",
            {"path": "briefs/partial.md", "content": drafted["brief"]},
        )
        self.assertIsNone(write)

    def test_web_fallback_completes_without_web_extract(self) -> None:
        script = (
            ROOT
            / "agents"
            / "research-bot"
            / "skills"
            / "web-fallback-fetch"
            / "SKILL.md"
        )
        front = script.read_text(encoding="utf-8")
        self.assertIn("fallback_for_tools: [web_extract]", front)
        self.pkg.tools.research_plan({"question": "fallback", "tier": "quick"})
        fetched = "Fallback body. The product launched in March after a quiet beta."
        added = json.loads(
            self.pkg.tools.evidence_add(
                {
                    "url": "https://example.com/fallback",
                    "title": "Fallback",
                    "text": fetched,
                    "origin": "web-fallback-fetch",
                }
            )
        )
        self.assertTrue(added.get("ok"))
        drafted = self.pkg.store.draft.draft_brief()
        self.assertIn("[S1]", drafted["brief"])
        blocked_extract = self.pkg.hooks.pre_tool_call(
            "write_file",
            {"path": "briefs/fallback.md", "content": drafted["brief"]},
        )
        self.assertIsNone(blocked_extract)

    def test_amber_named_gap_depth(self) -> None:
        created = json.loads(
            self.pkg.tools.research_plan(
                {
                    "question": "Compare A and B",
                    "tier": "standard",
                    "open_questions": ["Mandate A", "Mandate B"],
                }
            )
        )
        self.assertTrue(created.get("ok"))
        current = self.pkg.store.run.load_run()
        assert current is not None
        current["spend"]["tokens"] = int(current["budget"]["tokens"] * 0.65)
        current["governor"] = self.pkg.store.run.governor_state(current)
        current["named_gaps"] = ["Mandate A"]
        self.pkg.store.run.save_run(current)
        self.assertEqual(current["governor"], "AMBER")
        refused = json.loads(
            self.pkg.tools.worker_brief({"open_question": "Brand new batch topic"})
        )
        self.assertTrue(refused.get("error"))
        allowed = json.loads(self.pkg.tools.worker_brief({"open_question": "Mandate A"}))
        self.assertTrue(allowed.get("ok"))
        blocked_batch = self.pkg.hooks.pre_tool_call(
            "delegate_task",
            {"goal": "sweep the whole web for anything new"},
        )
        self.assertEqual((blocked_batch or {}).get("action"), "block")
        depth = self.pkg.hooks.pre_tool_call(
            "delegate_task",
            {"goal": "Mandate A only"},
        )
        self.assertIsNone(depth)

    def test_domain_soft_cap_modifies_search(self) -> None:
        self.pkg.tools.research_plan({"question": "domains", "tier": "quick"})
        current = self.pkg.store.run.load_run()
        assert current is not None
        current["domain_counts"] = {"example.com": 4}
        self.pkg.store.run.save_run(current)
        modified = self.pkg.hooks.pre_tool_call(
            "web_search",
            {"query": "widget recall 2026"},
        )
        self.assertEqual((modified or {}).get("action"), "modify")
        self.assertIn("-site:example.com", (modified or {}).get("args", {}).get("query", ""))

    def test_fetch_counter_and_index_search(self) -> None:
        self.pkg.tools.research_plan({"question": "index", "tier": "quick"})
        self.pkg.hooks.post_tool_call("web_search", {"query": "x"}, "hits", duration_ms=12)
        current = self.pkg.store.run.load_run()
        assert current is not None
        self.assertGreaterEqual(int((current.get("spend") or {}).get("fetches") or 0), 1)
        added = json.loads(
            self.pkg.tools.evidence_add(
                {
                    "url": "https://example.com/widget-recall",
                    "title": "Widget recall 2026",
                    "text": "The widget recall started in March 2026 after a 12% failure rate.",
                    "quote": "12% failure rate",
                }
            )
        )
        self.assertTrue(added.get("ok"))
        found = json.loads(self.pkg.tools.evidence_search({"query": "widget recall"}))
        self.assertGreaterEqual(found["count"], 1)
        self.assertEqual(found["cards"][0]["id"], "S1")

    def test_docs_query_requires_openable_url(self) -> None:
        self.ctx.mcp_responses["context7:query-docs"] = {"ok": True, "result": "no url here"}
        raw = json.loads(self.pkg.tools.docs_query({"library_id": "/x", "query": "y"}))
        self.assertFalse(raw.get("ledger"))
        self.assertEqual(self.pkg.store.ledger.list_sources(), [])


if __name__ == "__main__":
    unittest.main()
