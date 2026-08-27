---
name: literature-review
description: "Load when the user wants a literature review, survey, or what the docs and papers actually say."
version: 1.0.0
metadata:
  hermes:
    tags: [research, literature, context7]
    category: research
    related_skills: [source-triage, claim-check]
    requires_toolsets: [research-bot]
    requires_tools: [resolve_library, docs_query, cite_source]
---

# Literature review

## When to Use

The user wants a survey of what primary docs and papers actually say — not a product implementation.

## Quick Reference

| Step | Tool |
| --- | --- |
| Resolve a library ID | `resolve_library` |
| Read that library's docs | `docs_query` |
| Record a web/arXiv page you opened | `source_ledger_add` |
| See what is already recorded | `source_ledger_list` |
| After every claim | `cite_source` |

Never call raw `mcp_*` / `mcp_context7_*` tools. The research-bot plugin registered the facade tools. Do not put `CONTEXT7_API_KEY` in this skill.

## Procedure

1. Name the library, paper, or product.
2. If it is a documented library, call **`resolve_library`**, then **`docs_query`** with the returned library ID. Prefer `/nousresearch/hermes-agent` when the subject is Hermes.
3. Open official LLM entry points when they exist (Hermes: `https://hermes-agent.nousresearch.com/llms.txt`).
4. After each non-Context7 page you actually opened, call **`source_ledger_add`** with the URL, title, and a short quote you saw.
5. Mid-review, call **`source_ledger_list`**.
6. After every factual claim, call **`cite_source`** and only paste those formatted entries.
7. If Context7 and the official page disagree, record both and treat the official page as primary.

## Pitfalls

- Do not invent knobs, flags, or endpoints from training data.
- A 404 or empty Context7 hit is a finding. Say so.
- Do not write product code. Findings go under `notes/`, `research/`, `briefs/`, or a `.md` artifact.
- Missing env vars do not hide this skill. Context7 auth is the plugin's `ctx.call_mcp`, not a skill env key.

## Verification

Every factual sentence maps to a ledger source from `cite_source`, or is labeled inference.
