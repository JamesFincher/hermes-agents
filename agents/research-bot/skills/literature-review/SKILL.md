---
name: literature-review
description: Survey primary sources into the research-bot ledger. Use when the user wants a literature review, survey, or "what do the docs and papers say?"
version: 1.0.0
metadata:
  hermes:
    tags: [research, literature, context7]
    category: research
    requires_toolsets: [research-bot]
    requires_tools: [source_ledger_add, source_ledger_list, source_ledger_cite]
---

# Literature review

## When to Use

The user wants a survey of what primary docs and papers actually say — not a product implementation.

## Procedure

1. Name the library, paper, or product. If it is Hermes or Honcho, query Context7 first:
   - `/nousresearch/hermes-agent`
   - `/plastic-labs/honcho`
   - Also useful: `/llmstxt/hermes-agent_nousresearch_llms_txt`, `/websites/honcho_dev_v3`
2. Then open official LLM entry points when they exist (Hermes: `https://hermes-agent.nousresearch.com/llms.txt`).
3. Prefer first-party pages, specs, and papers over blogs.
4. **After each retrieved source, call `source_ledger_add`** with the URL, title, and a short quote you actually saw. Do not add a source you did not open.
5. Mid-review, call **`source_ledger_list`** to see what is already recorded before fetching more.
6. When writing the survey, call **`source_ledger_cite`** and only paste those formatted entries. Never invent bibliography rows.
7. If Context7 and the official page disagree, record both and treat the official page as primary.

## Pitfalls

- Do not invent knobs, flags, or endpoints from training data.
- A 404 or empty Context7 hit is a finding. Say so.
- Do not clone third-party repos unless the user asked for a local checkout.
- Do not write product code. Findings go under `notes/`, `research/`, `briefs/`, or a `.md` artifact.

## Verification

Every factual sentence maps to a ledger source from `source_ledger_cite`, or is labeled inference.
