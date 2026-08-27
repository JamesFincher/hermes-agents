# HDR honest limits

State these in the shipped docs. A spec that hides its edges produces a profile that lies about them.

- `pre_verify` does not fire for markdown-only turns. The Citation Gate is a `pre_tool_call` block on the brief write. A user who reads the answer in chat without a file write bypasses it. Mitigation: `transform_llm_output` flags uncited statistics inline.
- `claim_verify` proves a span exists in a retrieved document. It does not prove the document is right, or that the span means what the claim says. It moves the failure mode from fabrication to misreading.
- Source tiering is a heuristic over domains and metadata. It will misclassify a good preprint and flatter a bad institutional blog.
- The Evidence Bus can only distil what the extractor returned. A page that renders its substance in canvas or images degrades to `vision_analyze`, which is lossy and costs tokens.
- Prompt-injection handling is defence in depth, not a proof. The Docker backend is the boundary that matters. The sanitizer only reduces frequency.
- Children write to the shared profile-home ledger. Official pages document `plugin-data/` under `HERMES_HOME` and live transcripts under `<hermes_home>/cache/delegation/live/…`. The transcript-grep backstop stays because no sentence says the child process `getenv` equals the parent.
- Budget numbers in the spec are starting points. P10 fixtures track tokens per tier-A/B source. They are not yet field measurements.
- Cross-model MoA verification is only as good as the second model's independence. Official MoA is a **provider**, not a toolset. This profile does not invent a `moa` toolset.
- Official GitHub-URL install copies the repo root as one payload. This library has many profiles. Path install is the supported path. There is no official multi-profile index.
