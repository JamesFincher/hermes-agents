---
name: claim-check
description: "Load before asserting a fact, delivering a brief, or when a citation looks unsourced."
version: 1.0.0
metadata:
  hermes:
    tags: [research, citations, integrity]
    category: research
    related_skills: [literature-review, source-triage]
    requires_toolsets: [research-bot]
    requires_tools: [resolve_library, docs_query, cite_source]
---

# Claim check

## When to Use

Before a research brief, literature summary, or any answer that names a paper, docs page, version, or "as documented" fact.

## Quick Reference

| Step | Tool |
| --- | --- |
| Test a claim | `source_ledger_check` |
| After every claim you keep | `cite_source` |
| Fill a docs gap | `resolve_library` then `docs_query` |
| Find a missing primary on the open web | `web_search` then `web_extract` |

Never call raw `mcp_*` tools. The research-bot plugin registers the `resolve_library`, `docs_query`, and `cite_source` tools. After every claim you keep, call `cite_source`. Do not put `CONTEXT7_API_KEY` in this skill.

## Procedure

1. List claims a skeptical reader would ask "says who?"
2. For each claim, call **`source_ledger_check`** with the claim text.
3. If the tool returns no supporting overlap, do not state the claim as fact. Retrieve a primary page. Use **`resolve_library`** / **`docs_query`** for library docs. Use **`web_search`** then **`web_extract`** for the open web. Then call **`source_ledger_add`**, or drop/relabel the claim.
4. After every claim you keep, call **`cite_source`** for those ledger IDs and use only that formatted text.
5. Never generate a plausible-looking citation. Do not invent a ranker tool.

## Pitfalls

- Training data is not a citation.
- Lexical overlap from `source_ledger_check` is not proof — open the URL.
- `cite_source` with an empty ledger means you have nothing to cite. Say so.

## Verification

Read the draft once. Every bibliographic entry exists in the latest `cite_source` result.
