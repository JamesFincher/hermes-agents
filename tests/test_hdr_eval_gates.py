"""CI deterministic gates from HDR spec §10. Fixture-only."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from evals.gates import all_fixture_runs, check_run
from evals.rubric import score_brief, score_run_dir
from evals.run_offline import run_all

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"


class EvalGateTests(unittest.TestCase):
    def test_twelve_questions(self) -> None:
        payload = json.loads((EVALS / "questions.json").read_text(encoding="utf-8"))
        questions = payload["questions"]
        self.assertEqual(len(questions), 12)
        tiers = [row["tier"] for row in questions]
        self.assertEqual(tiers.count("standard"), 4)
        self.assertEqual(tiers.count("deep"), 6)
        self.assertEqual(tiers.count("exhaustive"), 2)
        kinds = {row["kind"] for row in questions}
        for needed in (
            "contradiction",
            "no-source",
            "pdf",
            "paywall",
            "dead-link",
            "time-sensitive",
            "multi-entity",
        ):
            self.assertIn(needed, kinds)

    def test_three_fixture_runs_pass_gates(self) -> None:
        runs = all_fixture_runs()
        self.assertGreaterEqual(len(runs), 3)
        kinds = {"run_a": "contradiction", "run_b": "paywall", "run_c": "dead-link"}
        means = []
        for run_dir in runs:
            errors = check_run(run_dir)
            self.assertEqual(errors, [], msg=f"{run_dir.name}: {errors}")
            scored = score_run_dir(run_dir, kinds.get(run_dir.name, "survey"))
            means.append(scored["mean"])
        self.assertGreaterEqual(sum(means) / len(means), 2.4)

    def test_twelve_questions_complete_offline(self) -> None:
        payload = run_all()
        self.assertEqual(payload["total"], 12)
        self.assertEqual(payload["completed"], 12)
        scores = []
        for row in payload["results"]:
            scored = score_brief(
                brief=row["brief"],
                kind=row["kind"],
                gate_errors=row.get("gate_errors") or [],
            )
            scores.append(scored["mean"])
            self.assertTrue(row["brief"].strip())
        self.assertGreaterEqual(sum(scores) / len(scores), 2.4)


if __name__ == "__main__":
    unittest.main()
