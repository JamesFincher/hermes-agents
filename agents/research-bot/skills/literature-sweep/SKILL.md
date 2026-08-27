---
name: literature-sweep
description: Academic sweep via scholar_search plus Crossref, Unpaywall, and PDF text scripts.
version: 2.0.0
metadata:
  hermes:
    tags: [Research, Literature, Papers]
    requires_toolsets: [hdr]
    requires_tools: [scholar_search, evidence_add, cite_source]
    required_environment_variables: [CROSSREF_MAILTO, UNPAYWALL_EMAIL]
    related_skills: [deep-research-run, web-fallback-fetch]
---

# Literature sweep

Find papers. Prefer DOI and an open copy. Extract PDF text with a script, not a rewritten parser.

## When to Use

Use this when the question is academic or the user asks what the literature says.
Do not use this as the whole research loop.

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/crossref.py" "query"
python "${HERMES_SKILL_DIR}/scripts/unpaywall.py" "10.1234/example"
python "${HERMES_SKILL_DIR}/scripts/pdf_text.py" data/paper.pdf
```

Or call `scholar_search` and then `evidence_add`.

## Procedure

Call `scholar_search` with the topic. It returns cards with DOI and an OA link when Unpaywall can see one.
If the tool is thin, run `${HERMES_SKILL_DIR}/scripts/crossref.py`.
For a DOI behind a paywall, run `${HERMES_SKILL_DIR}/scripts/unpaywall.py`. Cite the abstract and mark paywall if no OA copy.
For a PDF, run `${HERMES_SKILL_DIR}/scripts/pdf_text.py`, then `evidence_add` with the extracted text.
`resolve_library` and `docs_query` are for SDK docs, not papers.
`web_search` / `web_extract` are the web ladder, not the literature spine.
Do not call raw `mcp_*` tools. There is no official OpenAlex or PubMed Hermes server in this profile.

## Pitfalls

Do not invent a DOI. Do not cite Context7 as a paper.
`CROSSREF_MAILTO` and `UNPAYWALL_EMAIL` come from the host env. Skills pass them into Docker.

## Verification

Each paper card has an openable URL (DOI or OA).
PDF text is in the corpus before you cite it.
`cite_source` includes author and year when the ledger has them.
