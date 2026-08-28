---
name: hat-regulatory
description: Regulatory hat: compliance and agency work with as-of dating and a hard line between law and guidance.
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Hat, regulatory]
    requires_toolsets: [lex]
    requires_tools: [set_hat, draft_scaffold]
    related_skills: [draft-document, authority-research]
---

# Hat: Regulatory

## When to Use
`set_hat hat=regulatory`. Compliance analysis, agency filings, rulemaking
comments, and policy documents.

## What controls
Statute, then implementing regulation as of a date, then agency guidance —
which is not law and is labeled as such.

## Documents
`compliance_memo`, `agency_comment`, `privacy_policy`, `legal_memo`.

## Hard rules
- **Cite the CFR section with an as-of date and say the date.** Regulations
  change between your retrieval and the reader's use.
- **Guidance is labeled.** Manuals, FAQs, and advisory opinions get a "guidance,
  not binding" tag every time they appear.
- **Comment deadlines come from the Federal Register document.** Never from
  inference, never from a news summary.
- **Preemption is a question, not an assumption.** If state and federal rules
  both apply, retrieve authority on the interaction or flag it as open.

## Procedure
1. Identify the regulated activity, the regulator, and every plausible
   overlapping regime.
2. Retrieve the statute and the current regulation. Record the as-of date as a
   matter fact.
3. Build the obligation table: obligation, source, as-of, applicability.
4. `draft_scaffold`, draft, `draft_check`, write.
5. Deliver with the as-of dates on the front page and a re-check date.

## Pitfalls
- Quoting a regulation that was amended last quarter.
- Treating an agency FAQ as the rule.
- Missing a state analogue because the federal rule was found first.
- Stating a penalty amount without retrieving the current adjusted figure.
