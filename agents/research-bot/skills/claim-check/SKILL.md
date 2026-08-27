---
name: claim-check
description: Test a factual claim against the research-bot ledger. Use before asserting a fact, delivering a brief, or when a citation looks unsourced.
version: 1.0.0
metadata:
  hermes:
    tags: [research, citations, integrity]
    category: research
    requires_toolsets: [research-bot]
    requires_tools: [source_ledger_check, source_ledger_cite]
---

# Claim check

## When to Use

Before a research brief, literature summary, or any answer that names a paper, docs page, version, or "as documented" fact.

## Procedure

1. List claims a skeptical reader would ask "says who?"
2. For each claim, call **`source_ledger_check`** with the claim text.
3. If the tool returns no supporting overlap, do not state the claim as fact. Retrieve a primary page (`source_ledger_add`) or drop/relabel the claim.
4. When the claim is supported, call **`source_ledger_cite`** for those ledger IDs and use only that formatted text.
5. Never generate a plausible-looking citation. No fake authors, titles, years, DOIs, or quote marks around remembered text.
6. When quoting, use words from the retrieved page. If you only have a paraphrase, say it is a paraphrase.

## Pitfalls

- Training data is not a citation.
- Lexical overlap from `source_ledger_check` is not proof — open the URL.
- Version numbers guessed from "current knowledge" are invented citations.
- `source_ledger_cite` with an empty ledger means you have nothing to cite. Say so.

## Verification

Read the draft once. Every bibliographic entry exists in the latest `source_ledger_cite` result.
