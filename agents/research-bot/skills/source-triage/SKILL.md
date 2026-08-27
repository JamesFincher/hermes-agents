---
name: source-triage
description: Rank retrieved sources and record only primaries in the ledger. Use when the user has a pile of links, search hits, or mixed-quality citations to sort.
version: 1.0.0
metadata:
  hermes:
    tags: [research, sources, triage]
    category: research
    related_skills: [literature-review, claim-check]
    requires_toolsets: [research-bot]
    requires_tools: [resolve_library, docs_query, source_ledger_add, source_ledger_list, source_ledger_cite]
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
| Formatted citations | `source_ledger_cite` |

Never call raw `mcp_*` tools.

## Procedure

1. Call **`source_ledger_list`** first so you do not re-add sources already recorded.
2. Open each candidate. A snippet is not a retrieve — read the page.
3. Rank: **Primary** (vendor docs, spec, paper) / **Supporting** / **Skip**.
4. For every source you actually opened and will use, call **`source_ledger_add`**. If the source is a library docset, resolve and query via **`resolve_library`** / **`docs_query`** instead of raw MCP.
5. Drop unread or low-quality items. Say what you skipped and why.
6. Hand the ranked set back with **`source_ledger_cite`**. Do not write product code.

## Pitfalls

- Do not add a URL you did not open.
- Training-data "I recall a paper titled…" is not a source.
- When two pages conflict, keep both in the ledger and say which is primary.

## Verification

`source_ledger_list` shows only pages you retrieved. Rank labels match the page type.
