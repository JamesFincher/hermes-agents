# research-bot deep dive (HDR v2)

## 1. Title and disclaimer

This file describes **research-bot HDR v2 as shipped**. The repo is [JamesFincher/hermes-agents](https://github.com/JamesFincher/hermes-agents). The spec is [`HDR-SPEC.md`](HDR-SPEC.md). Facts are [`HERMES-FACTS.md`](HERMES-FACTS.md). Limits are [`HONEST-LIMITS.md`](HONEST-LIMITS.md).

This is not training data. Knobs come from official Hermes pages cited in HERMES-FACTS, or from this profile's files.

The profile is not installed until:

```bash
hermes profile install ./agents/research-bot --alias
```

That command copies `agents/research-bot/` into `~/.hermes/profiles/research-bot/`. That directory becomes `HERMES_HOME`.

Later profiles follow [`PROFILE-PLAYBOOK.md`](PROFILE-PLAYBOOK.md). Do not copy this plugin, these tools, or these skills.

---

## 2. What it is

**research-bot** is one independent **profile**. A profile is a separate `HERMES_HOME`. Official: [Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles/).

It plans. It fans out. It verifies. It writes cited briefs. It does not implement product code.

v1 was a citation-etiquette layer. v2 is Hermes Deep Research. The loop is: clarify → plan → breadth workers → Evidence Bus → `gap_scan` → depth → synthesize from the ledger only → verify.

This repo is the **Hermes Agent Profile Library**. Grow it by adding `agents/<name>/`.

---

## 3. Five surfaces

Never collapse these four official names: skill, tool, plugin, MCP. SOUL is identity.

| Surface | This profile |
| --- | --- |
| **SOUL** | Investigator text. No tool names. No paths. No MCP. |
| **SKILL** | Five disjoint recipes under `skills/`. |
| **TOOL** | Builtins plus tools the hdr plugin registers. |
| **PLUGIN** | `plugins/hdr/` — `plugin.yaml` + `register(ctx)`. Not a tool. |
| **MCP** | Context7 only. Facades: `resolve_library`, `docs_query`. |

Say: "the hdr plugin registers the `research_plan` tool."

---

## 4. Config that matters

`config.yaml` sets context economics, Docker terminal, keyless rescue, browser CDP, and the research toolset bundle.

Bundle: `web`, `browser`, `vision`, `file`, `terminal`, `code_execution`, `skills`, `memory`, `session_search`, `todo`, `clarify`, `delegation`, `cronjob`, `hdr`.

Official STOP: there is no `moa` toolset. MoA is provider `moa`. See HERMES-FACTS.

`tools.include` is omitted. Empty include is not documented as unset. `enabled: false` on MCP would break `ctx.call_mcp`.

`proactive_prune_tokens: 48000`. `compression.in_place: true`. `prompt_caching.cache_ttl: "1h"`. `agent.run_budget_seconds: 1800`. `agent.max_turns: none`.

`terminal.backend: docker`. A research agent reads untrusted pages.

Do not pin `model.default` in git. Set the frontier planner and the cheap worker on the host.

---

## 5. The loop

1. **Plan.** `research_plan` writes `plugin-data/hdr/run.json`. Budget is a table, not a guess.
2. **Breadth.** `worker_brief` then `delegate_task`. One mandate each. Children skip SOUL.
3. **Evidence Bus.** `transform_tool_result` stores the page, returns a card ≤400 tokens.
4. **Gap.** `gap_scan` returns saturation. The model does not estimate it.
5. **Depth.** Targeted workers on named gaps. AMBER blocks new batches and still allows a named-gap brief.
6. **Synthesize.** Ledger only. No network.
7. **Verify.** `claim_verify`, `conflict_report`, `cite_source`. Bibliography is appended by `transform_llm_output`.

---

## 6. Evidence Bus

Canonicalize the URL. Write `corpus/<sha256>.txt`. Extract metadata. Score a tier. Keep ≤3 quote spans of ≤25 words. The model sees a card.

`pre_tool_call` blocks a second fetch of the same canonical URL and returns the card id.

Fail open: a broken hook returns `None`. The original result flows through.

---

## 7. Policy and governor

Write allowlist: `notes/ research/ briefs/ findings/ citations/ sources/ data/`. Any extension inside. Nothing outside.

Citation Gate: `[S#]` must resolve. A statistic, date, quantity, or quote needs a marker.

Governor: GREEN / AMBER / RED / HARD from token, fetch, and wall ratios. Pair with `agent.run_budget_seconds`. AMBER blocks new `delegate_task` batches. RED blocks network tools. HARD leaves ledger tools and brief writes.

---

## 8. Fan-out

`delegation.max_concurrent_children: 5`. `max_spawn_depth: 2`. Cheap child model is a host setting.

`worker_harvest` returns counts and ids. Zero raw page text in the parent. Transcript backstop: `<hermes_home>/cache/delegation/live/<delegation_id>/task-<n>.log`.

---

## 9. Skills

| Skill | Trigger |
| --- | --- |
| `deep-research-run` | Broad question |
| `source-triage` | Pasted URLs |
| `claim-audit` | Check this draft |
| `literature-sweep` | What does the literature say |
| `web-fallback-fetch` | `web_extract` missing |

Scripts run via `${HERMES_SKILL_DIR}`. `skills.inline_shell: false`.

---

## 10. Eval

`evals/` holds 12 frozen questions and three fixture runs. CI runs deterministic gates: no unresolvable `[S#]`, no unmarked statistics, no unsupported cited claims, no duplicate fetches, no orphan corpus files, tokens per A/B source ≤ 8k on fixtures. The LLM judge is nightly, not per commit.

---

## 11. Install note

GitHub-URL install of this repo cannot see a multi-profile index. Official install copies repo root as one payload. Use the path command above.

`hermes_requires` is `>=0.13.0` (documented example). `>=0.14.0` was unverified and removed.
