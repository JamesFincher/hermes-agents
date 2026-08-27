---
name: deep-research-run
description: Full HDR loop for a broad question — plan, fan out, verify, brief.
version: 2.0.0
metadata:
  hermes:
    tags: [Research, Deep Research, Orchestration]
    requires_toolsets: [hdr, delegation, web]
    requires_tools: [research_plan, gap_scan, cite_source, delegate_task]
    related_skills: [source-triage, claim-audit]
---

# Deep research run

Run the six-phase HDR loop. Plan first. Fan out. Verify. Write a cited brief.

## When to Use

Use this when the user asks to research a broad or multi-part question.
Use this for due diligence, surveys, and "what is the state of X".
Do not use this for a single pasted URL list (use source-triage).
Do not use this for a draft already written (use claim-audit).

## Quick Reference

1. Call `research_plan` with the question, tier, open questions, and falsifiers.
2. For each open question, call `worker_brief`, then `delegate_task`.
3. Call `worker_harvest` when a child finishes. Expect ids and counts only.
4. Call `gap_scan`. Trust the saturation number. Do not guess it.
5. Synthesize from the ledger only. Then `claim_verify` and `cite_source`.
6. Write the brief under `briefs/` or `research/`.

## Procedure

Call `clarify` once if scope is ambiguous, then proceed.

Create the run with `research_plan`. Pick `quick`, `standard`, `deep`, or `exhaustive` from the user's ask. `exhaustive` only if they said so.

In breadth, give each child one open question and an explicit boundary. Paste the `worker_brief` text into `delegate_task`. Use `background=true` for the batch. Children skip SOUL. Do not fetch in the parent during synthesis.

Use `web_search` and `web_extract` on the workers. Use `resolve_library` and `docs_query` only for library or SDK docs. Those tools must return an openable URL or they do not enter the ledger. Do not call raw `mcp_*` tools.

After each batch, `gap_scan`. If it recommends depth, spawn targeted workers on named gaps. If it recommends synthesize or stop, stop fetching.

Synthesis reads cards via `evidence_search` and slices via `evidence_read`. No `web_extract` in phase 5.

Verify with `claim_verify` and `conflict_report`. Then `cite_source`. Write the brief. The Citation Gate blocks unresolvable `[S#]` markers and unmarked statistics.

## Pitfalls

Do not invent citations. Do not average disagreements.
Do not re-fetch a URL already in the corpus. The dedupe fence will block it.
Do not put findings in memory. Findings live in the ledger.
Do not start fifty workers for a one-fact question.

## Verification

`gap_scan` returned a saturation number.
Every `[S#]` in the brief resolves.
`claim_verify` has no unsupported load-bearing claim.
The governor state is visible in the digest.
