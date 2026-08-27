---
name: web-fallback-fetch
description: Fetch a page when web_extract is missing. Curl, readability, then Wayback.
version: 2.0.0
metadata:
  hermes:
    tags: [Research, Fetch, Fallback]
    requires_toolsets: [hdr]
    requires_tools: [archive_lookup, evidence_add]
    fallback_for_tools: [web_extract]
    related_skills: [literature-sweep, source-triage]
---

# Web fallback fetch

This skill appears when `web_extract` is missing. Fetch the page another way. Store the text.

## When to Use

Use this only when the primary extractor is gone or failed.
Hermes shows this skill via `fallback_for_tools: [web_extract]`.

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/fetch_page.py" "https://example.com/page"
```

Then `evidence_add` the saved text. If the live page is dead, call `archive_lookup`.

## Procedure

Run `${HERMES_SKILL_DIR}/scripts/fetch_page.py` with the URL.
If that fails, try `browser_navigate` + `browser_snapshot` when the browser toolset is up.
If the link is dead, call `archive_lookup` and cite both the original and the archived URL.
Pass the saved body to `evidence_add`. The Evidence Bus stores the corpus.
Do not pipe `curl` to a shell.
Do not call raw `mcp_*` tools.
`web_search` can still list hits. This skill replaces extract, not search.

## Pitfalls

A canvas-only page needs `vision_analyze`. Text fetch will be empty.
Paywalls: cite the abstract and mark `fetch_status` paywall. Do not invent the body.

## Verification

`evidence_add` returned a source id.
The corpus file is byte-exact with the saved body.
The brief cites the archived URL when the live URL is gone.
