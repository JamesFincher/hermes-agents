---
name: source-triage
description: "Load when the user has a pile of links, search hits, or mixed-quality citations to rank."
version: 1.0.0
metadata:
  hermes:
    tags: [research, sources, triage]
    category: research
    related_skills: [literature-review, claim-check]
    requires_toolsets: [research-bot]
    requires_tools: [resolve_library, docs_query, cite_source]
---

# Source triage

## When to Use

The user dumped URLs, search results, or a draft bibliography and needs them ranked: primary vs commentary, retrieved vs unread.

## Quick Reference

| Step | Tool |
| --- | --- |
| See recorded sources | `source_ledger_list` |
| Record a page you opened | `source_ledger_add` |
| Library docs (not raw MCP) | `resolve_library` then `docs_query` |
| After every claim | `cite_source` |

Never call raw `mcp_*` tools. Do not put `CONTEXT7_API_KEY` in this skill.

## Procedure

1. Call **`source_ledger_list`** first so you do not re-add sources already recorded.
2. Open each candidate. A snippet is not a retrieve — read the page.
3. Rank: **Primary** (vendor docs, spec, paper) / **Supporting** / **Skip**.
4. For every source you actually opened and will use, call **`source_ledger_add`**. If the source is a library docset, resolve and query via **`resolve_library`** / **`docs_query`** instead of raw MCP.
5. Drop unread or low-quality items. Say what you skipped and why.
6. After every claim in the ranked set, call **`cite_source`**. Do not write product code.

## Pitfalls

- Do not add a URL you did not open.
- Training-data "I recall a paper titled…" is not a source.
- When two pages conflict, keep both in the ledger and say which is primary.

## Verification

`source_ledger_list` shows only pages you retrieved. Rank labels match the page type. Every kept claim has a `cite_source` entry.
