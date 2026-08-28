# HDR honest limits

State these in the shipped docs. A spec that hides its edges produces a profile that lies about them.

- `pre_verify` does not fire for markdown-only turns. The Citation Gate is a `pre_tool_call` block on the brief write. A user who reads the answer in chat without a file write bypasses it. Mitigation: `transform_llm_output` flags uncited statistics inline.
- `claim_verify` proves a span exists in a retrieved document. It does not prove the document is right, or that the span means what the claim says. It moves the failure mode from fabrication to misreading.
- Source tiering is a heuristic over domains and metadata. It will misclassify a good preprint and flatter a bad institutional blog.
- The Evidence Bus can only distil what the extractor returned. A page that renders its substance in canvas or images degrades to `vision_analyze`, which is lossy and costs tokens.
- Prompt-injection handling is defence in depth, not a proof. The Docker backend is the boundary that matters. The sanitizer only reduces frequency.
- Children write to the shared profile-home ledger. P0 resolved profile-home `plugin-data/` and live transcripts as `[DOC]`. The transcript-grep backstop stays.
- Budget numbers in the spec are starting points. P10 fixtures track tokens per tier-A/B source. They are not yet field measurements.
- Two clocks exist. `agent.run_budget_seconds: 1800` is the Hermes host backstop. Official docs say it resets on each user message and injects a one-time wrap-up at 80%. The HDR governor uses `TIER_BUDGET.seconds` (90 / 360 / 1200 / 3600) from `started_at`. Exhaustive's 3600 s envelope is longer than the 1800 s host wrap-up. There is no per-tier Hermes knob.
- HARD still allows writes under the seven-dir allowlist: `notes/ research/ briefs/ findings/ citations/ sources/ data/`. The automatic HARD brief is `plugin-data/hdr/briefs/<run_id>-partial.md`.
- Child API hooks are not a guaranteed share of parent `run.json`. `subagent_stop` folds `usage` / `tokens` when the payload includes them. If the child already incremented the same `api_request_id`, the parent skips a second add.
- `delegation.model` is host-set. Empty inherits the parent. The digest then warns: "workers inherit parent — cost warning."
- Cross-model MoA verification is only as good as the second model's independence. Official MoA is a **provider**, not a toolset. This profile does not invent a `moa` toolset.
- Official GitHub-URL install copies the repo root as one payload. This library has many profiles. Path install is the supported path. There is no official multi-profile index.
