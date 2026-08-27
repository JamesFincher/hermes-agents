---
name: source-triage
description: Rank retrieved sources and record only primaries in the ledger. Use when the user has a pile of links, search hits, or mixed-quality citations to sort.
version: 1.0.0
metadata:
  hermes:
    tags: [research, sources, triage]
    category: research
    requires_toolsets: [research-bot]
    requires_tools: [source_ledger_add, source_ledger_list]
---

# Source triage

## When to Use

The user dumped URLs, search results, or a draft bibliography and needs them ranked: primary vs commentary, retrieved vs unread.

## Procedure

1. Call **`source_ledger_list`** first so you do not re-add sources already recorded.
2. Open each candidate. A snippet is not a retrieve — read the page.
3. Rank:
   - **Primary** — vendor docs, spec, paper, first-party API reference
   - **Supporting** — secondary writeup that cites a primary
   - **Skip** — unverifiable, marketing, or invented-looking
4. For every source you actually opened and will use, call **`source_ledger_add`** (`kind`: `docs`, `paper`, `source`, or `web`). Include a quote from the page.
5. Drop unread or low-quality items. Say what you skipped and why.
6. Hand the ranked set back. Do not write product code from the triage.

## Pitfalls

- Do not add a URL you did not open.
- Training-data "I recall a paper titled…" is not a source. Skip it.
- When two pages conflict, keep both in the ledger and say which is primary.

## Verification

`source_ledger_list` shows only pages you retrieved. Rank labels match the page type.
