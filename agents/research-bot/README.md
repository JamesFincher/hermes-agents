# research-bot

HDR v2. Plans, fans out, verifies, and writes cited research briefs. Does not write product code.

This profile is one shelf item in the **Hermes Agent Profile Library**. Full walkthrough: [`docs/research-bot-deep-dive.md`](../../docs/research-bot-deep-dive.md). Limits: [`docs/HONEST-LIMITS.md`](../../docs/HONEST-LIMITS.md). Facts: [`docs/HERMES-FACTS.md`](../../docs/HERMES-FACTS.md). Spec: [`docs/HDR-SPEC.md`](../../docs/HDR-SPEC.md).

The plugin lives at `plugins/hdr/` (toolset `hdr`). Skills live in `skills/`. The next profile does not inherit them.

Memory provider is honcho (`memory.provider`). It is not a `plugins.enabled` entry.

Kanban text (`profile.yaml`):

> Plans, fans out, verifies, and writes cited research briefs. Does not write product code.

## Install (local path)

Official GitHub-URL install copies the **repo root** as one payload. This repo has many profiles. There is no official multi-profile index. Do not invent one. Install the path:

```bash
hermes profile install ./agents/research-bot --alias
```

That copies this directory, including `plugins/hdr/`, into `~/.hermes/profiles/research-bot/`. That directory is `HERMES_HOME`.

Override the name if `research-bot` already exists:

```bash
hermes profile install ./agents/research-bot --name research-bot-test --alias
```

Reserved names: `hermes`, `test`, `tmp`, `root`, `sudo`.

## After install

1. Copy env keys from `.env.EXAMPLE` into the profile `.env`. See **env_requires**.
2. Copy `honcho.json.example` to `honcho.json` (or merge the `hermes.research-bot` host). Never commit `honcho.json`. `honcho.json.example` is JSON, so it cannot hold a comment. `pinUserPeer: true` is official and gateway-only. The CLI ignores it. Do not add a `_comment` key.
3. `hermes memory setup` if needed. `hermes memory status` should show the provider active.
4. Confirm `plugins.enabled: [hdr]`. On Hermes 0.19.0, `hermes plugins` has no `doctor` action (choices: install, update, remove, list, enable, disable). Use `hermes -p research-bot plugins list` and `hermes -p research-bot tools list`.
5. `hermes -p research-bot tools list` (CLI form of `/tools list`) should show `web`, `browser`, `vision`, `file`, `terminal`, `code_execution`, `skills`, `memory`, `session_search`, `todo`, `clarify`, `delegation`, `cronjob`, `hdr`. There is **no `moa` toolset**. MoA is a provider.
6. Pin `/review` on the host with `auxiliary.review.model`. Set `delegation.model` on the host to a cheap worker. Empty inherits the parent. This profile does not invent a model id.

`mcp.json` and `config.yaml` `mcp_servers` must stay twins. Do not delete either file.

## Update

```bash
hermes profile update research-bot
```

`distribution_owned` includes `plugins/`. `plugin-data/` survives the update. Ledger schema migrates on load.

## env_requires

Host env only. Never commit values.

| Variable | Required | Why |
| --- | --- | --- |
| `HONCHO_API_KEY` | no | Cloud memory. Self-hosted uses `honcho.json` `baseUrl`. |
| `CONTEXT7_API_KEY` | no | Context7 MCP header. Library docs only. |
| `SEARXNG_URL` | deploy host | `web.search_backend: searxng`. |
| `FIRECRAWL_API_URL` | deploy host | `web.extract_backend: firecrawl`. Key optional when this URL is set. |
| `HERMES_CDP_URL` | no | `browser.cdp_url`. Our name, not a Hermes-defined env. |
| `UNPAYWALL_EMAIL` | no | Literature HTTP fallback. Auto-passed into Docker by skill env. |
| `CROSSREF_MAILTO` | no | Crossref polite pool. |
| `SEMANTIC_SCHOLAR_API_KEY` | no | Optional scholar HTTP. |
| Model provider key | deploy host | This profile does not pin `model.default`. Set the frontier planner and cheap worker on the host. Pin `/review` with `auxiliary.review.model`. Also set `delegation.model` on the host. Empty inherits the parent. Do not invent a model id. |

`web.keyless_fallback` and `web.keyless_rescue` are **true**. A dead primary path must degrade.

## Plugin (this profile only)

The hdr plugin registers tools on toolset `hdr`. It is not a tool. Do not copy it.

| Tool | When |
| --- | --- |
| `research_plan` | Start or update the run. Budget is computed. |
| `gap_scan` | After a batch. Returns saturation. |
| `evidence_add` / `search` / `read` / `stats` | Ledger and corpus. Cards, not pages. |
| `claim_verify` | Exact span. `source_ledger_check` is gone. |
| `citation_pass` | Maps claims, then `claim_verify`. Uses official `ctx.llm` when present. |
| `conflict_report` | Disagreements. Do not average. |
| `cite_source` | Only sanctioned bibliography. |
| `worker_brief` / `worker_harvest` | Child contract and counts-only harvest. |
| `resolve_library` / `docs_query` | Context7 facades. Openable URL or no ledger row. |
| `scholar_search` / `archive_lookup` | HTTP literature and Wayback. |

Hooks: Evidence Bus (`transform_tool_result`), policy (`pre_tool_call`), governor (`pre`/`post_api_request`), digest (`pre_llm_call` ≤1200 chars), bibliography (`transform_llm_output`).

Store: `<HERMES_HOME>/plugin-data/hdr/`.

`plugins/hdr/scripts/timeline.py` sorts dated lines. No skill recipe calls it. It is a helper, not a sixth skill. See `plugins/hdr/README.md`.

## Skills

Five disjoint skills. Frontmatter keys sit under `metadata.hermes`. Scripts use `${HERMES_SKILL_DIR}`.

1. `deep-research-run` — full loop. Needs `hdr`, `delegation`, `web`.
2. `source-triage` — pasted URLs. Script `dedupe_urls.py`.
3. `claim-audit` — draft check. Script `extract_claims.py` plus `claim_verify`.
4. `literature-sweep` — papers. Crossref / Unpaywall / PDF scripts.
5. `web-fallback-fetch` — `fallback_for_tools: [web_extract]`.

## Honest limits

These limits are also in [`docs/HONEST-LIMITS.md`](../../docs/HONEST-LIMITS.md).

- `pre_verify` does not fire for markdown-only turns. The Citation Gate is a `pre_tool_call` block on the brief write. A user who reads the answer in chat without a file write bypasses it. Mitigation: `transform_llm_output` flags uncited statistics inline.
- `claim_verify` proves a span exists in a retrieved document. It does not prove the document is right, or that the span means what the claim says. It moves the failure mode from fabrication to misreading.
- Source tiering is a heuristic over domains and metadata. It will misclassify a good preprint and flatter a bad institutional blog.
- The Evidence Bus can only distil what the extractor returned. A page that renders its substance in canvas or images degrades to `vision_analyze`, which is lossy and costs tokens.
- Prompt-injection handling is defence in depth, not a proof. The Docker backend is the boundary that matters. The sanitizer only reduces frequency.
- Children write to the shared profile-home ledger. Official pages document `plugin-data/` under `HERMES_HOME` and live transcripts under `<hermes_home>/cache/delegation/live/…`. The transcript-grep backstop stays.
- Budget numbers in the spec are starting points. P10 fixtures track tokens per tier-A/B source. They are not yet field measurements.
- Two clocks: Hermes `agent.run_budget_seconds: 1800` (per user message, wrap-up at 80%) and the HDR tier envelope on `started_at`. HARD writes a ledger-only brief under `plugin-data/hdr/briefs/`.
- Cross-model MoA verification is only as good as the second model's independence. Official MoA is a **provider**, not a toolset. This profile does not invent a `moa` toolset.
- Official GitHub-URL install copies the repo root as one payload. Path install is the supported path.
- Structure-only CI has no Hermes CLI. Live `hermes profile install` on Hermes 0.19.0 is recorded in [`evals/smoke/P1-LIVE.md`](../../evals/smoke/P1-LIVE.md). Offline tests cover the plugin, store, gates, and the 12-question fixture loop.
