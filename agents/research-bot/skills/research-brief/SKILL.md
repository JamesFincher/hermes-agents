---
name: research-brief
description: Write a cited research brief. Use when the user wants findings, not implementation — source review, comparison, or "what does the docs say?"
version: 1.0.0
metadata:
  hermes:
    tags: [research, writing, brief]
    category: research
    requires_toolsets: [file]
---

# Research brief

## When to Use

The deliverable is a written finding: what the sources say, what is unknown, and what that implies. Not a code change.

## Procedure

1. Restate the question in one sentence.
2. List sources actually retrieved (title + URL or paper id).
3. Findings — each bullet is a claim plus its source.
4. Gaps — what you looked for and did not find.
5. Implications — labeled as inference, not as documentation.
6. Stop. Do not implement product code, refactors, or "while I was here" patches.

## Pitfalls

- A brief that "also ships the fix" is out of role. Point at the finding; leave implementation to another profile.
- Do not pad with unsourced background.
- If sources conflict, show the conflict; do not silently pick a winner.

## Verification

A reader can open every cited URL and find the supporting sentence. No invented citations (use `citation-discipline`).
