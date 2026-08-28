# evals

`tasks.jsonl` — 12 frozen tasks. Eight normal, four adversarial (T09–T12).
The adversarial four are the ones that matter: they are direct attempts to make
the profile fabricate a citation, invent a fact, or obey an injected instruction.
A single fabrication on any of them fails the build.

`fixtures/` — recorded retrieval payloads so the deterministic gates in
`rubric.md` run offline in CI without hitting CourtListener.

Run the judged pass nightly, not per commit. Run the deterministic gates on
every commit.
