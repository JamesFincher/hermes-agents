---
name: matter-intake
description: Open a matter, fix jurisdiction and posture, and record the facts you were actually given before any drafting begins.
version: 1.0.0
metadata:
  hermes:
    tags: [Legal, Intake, Jurisdiction]
    requires_toolsets: [lex]
    requires_tools: [matter_open, matter_fact, set_hat]
    related_skills: [draft-document, authority-research]
---

# Matter Intake

## When to Use
Any legal request that has not yet been scoped: no jurisdiction, no forum, no
recorded facts. This runs before authority research and before drafting. If
`matter_open` has not been called, you are here.

## Quick Reference
| Field | Why it gates everything |
| --- | --- |
| jurisdiction | decides which law is binding and which is persuasive |
| forum | decides rules, formatting, deadlines, and mandatory forms |
| posture | decides which documents are even available |
| represented party | decides whose interests the drafting serves |
| hat | decides the document registry and the checklists |

## Procedure
1. Read the request and extract every fact you were **actually told**. Not
   inferred, not typical, not likely. Told.
2. Identify what is missing from the five fields above. If jurisdiction is
   missing and it changes the answer, use `clarify` **once**. Ask for the
   smallest set: jurisdiction, forum if a case is pending, and who you are
   drafting for.
3. `matter_open` with what you have.
4. `set_hat`. Then `skill_view` the matching `hat-*` skill.
5. `matter_fact` for each extracted fact, with its source (`user`, an exhibit
   path, a document id). A fact without a source is not recorded.
6. Record what you still need in the matter's open questions rather than
   guessing it. Everything unrecorded becomes a `[[FACT:...]]` placeholder in
   any draft — that is correct behavior, not a failure.
7. Say plainly, once, in your first substantive reply: this is not legal
   advice, and a licensed attorney in the jurisdiction must review it.

## Pitfalls
- **Assuming the state from context.** A user in one state may have a matter in
  another. Ask.
- **Recording an inference as a fact.** "The contract was probably signed in
  March" is not a fact. It is an open question.
- **Skipping the hat.** Without it, `draft_scaffold` refuses and you will be
  tempted to improvise a structure. Do not.

## Verification
`matter_open action=status` shows jurisdiction, hat, fact count, and open
questions. If any of the five fields is blank, intake is not finished.
