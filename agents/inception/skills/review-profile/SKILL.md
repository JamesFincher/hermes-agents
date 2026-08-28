---
name: review-profile
description: Score the PLAN first, then the tree. Isolation and surface-separation review using playbook §10 plus check_plan.
version: 1.1.0
metadata:
  hermes:
    tags: [Factory, Review, Isolation]
    requires_toolsets: [inception]
    requires_tools: [check_plan, check_profile]
    related_skills: [plan-profile, author-profile, probe-knob]
---

# Review a profile

Walk the plan, then the files. Return gaps, not vibes.

## When to Use

Use this when the user asks to review `agents/<name>/`, check isolation, or run the playbook §10 list.
Do not use this to author a new profile (use plan-profile, then author-profile).
Do not use this to probe a single knob (use probe-knob).

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/heuristic_list.py"
```

Then call `check_plan` on the name and `check_profile` on the path.

## Procedure

1. Call `check_plan` with `name`. If it is not ok, the review of the PLAN fails. Stop before scoring code.
2. Score the PLAN before the tree:

   - What is in context on turn 40 if the model is still planning? Prompted "docs first" is not a gate.
   - Which rules are prompted versus enforced? `check_plan` and the fence must do the work a paragraph cannot keep.
   - Does the failure ladder name what happens when Context7, the incumbent source, or an MCP is down?
   - Which surface does the work? If the canvas puts procedure in SOUL, fail the plan.

3. Call `check_profile` with `path` set to `agents/<name>/`. Treat JSON `gaps` as the structure baseline.
4. Print the heuristic list from `${HERMES_SKILL_DIR}/scripts/heuristic_list.py`.
5. Answer each item with evidence from the files:

   1. What is in context on turn 40? Walk SOUL, prompt sections, tool schemas, skill index, memory, last N tool results.
   2. What does the second call to the same expensive thing cost? Look for a fence or a cache.
   3. Which rules are prompted that a hook or a tool could enforce?
   4. What happens when the primary dependency is down? Read the failure ladder.
   5. What survives `/new`? The durable store must have a `version` field.
   6. What do the children return? If this profile rejected fan-out, say so.
   7. Where does untrusted text enter, and what sits between it and `terminal`?
   8. What would this profile confidently get wrong? Read `HONEST-LIMITS.md`.
   9. Which surface is doing the most work? If it is SOUL, the profile is a prompt wearing a directory.

6. Confirm the four surfaces stay separate. A plugin is a host package. A tool is a schema plus handler. A skill is a recipe. MCP is a backend.
7. Confirm the profile must not enable `hdr` and must not import `agents/research-bot`.

Do not call raw `mcp_*` tools. Use `docs_resolve` / `docs_ask` only when a review claim needs an official page.

## Pitfalls

A green `check_profile` does not prove the canvas matches the build.
A skipped `check_plan` is a review fail even if the tree validates.
Collapsed wording that treats a plugin as a tool is a review fail.
A missing `HONEST-LIMITS.md` is a law-11 fail.

## Verification

The PLAN score comes first. Prompted-versus-enforced is named.
Every heuristic has a one-line answer with a file citation.
`check_plan` and `check_profile` gaps are listed first.
The review names which of the five §4 patterns are present.
