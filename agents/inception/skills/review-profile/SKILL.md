---
name: review-profile
description: Isolation and surface-separation review of an existing agents/<name>/ using the playbook §10 heuristics.
version: 1.0.0
metadata:
  hermes:
    tags: [Factory, Review, Isolation]
    requires_toolsets: [inception]
    requires_tools: [check_profile]
    related_skills: [author-profile, probe-knob]
---

# Review a profile

Walk the nine heuristics. Return gaps, not vibes.

## When to Use

Use this when the user asks to review `agents/<name>/`, check isolation, or run the playbook §10 list.
Do not use this to author a new profile (use author-profile).
Do not use this to probe a single knob (use probe-knob).

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/heuristic_list.py"
```

Then call `check_profile` on the path.

## Procedure

1. Call `check_profile` with `path` set to `agents/<name>/`. Treat JSON `gaps` as the structure baseline.
2. Print the heuristic list from `${HERMES_SKILL_DIR}/scripts/heuristic_list.py`.
3. Answer each item with evidence from the files:

   1. What is in context on turn 40? Walk SOUL, prompt sections, tool schemas, skill index, memory, last N tool results.
   2. What does the second call to the same expensive thing cost? Look for a fence or a cache.
   3. Which rules are prompted that a hook or a tool could enforce?
   4. What happens when the primary dependency is down? Read the failure ladder.
   5. What survives `/new`? The durable store must have a `version` field.
   6. What do the children return? If this profile rejected fan-out, say so.
   7. Where does untrusted text enter, and what sits between it and `terminal`?
   8. What would this profile confidently get wrong? Read `HONEST-LIMITS.md`.
   9. Which surface is doing the most work? If it is SOUL, the profile is a prompt wearing a directory.

4. Confirm the four surfaces stay separate. A plugin is a host package. A tool is a schema plus handler. A skill is a recipe. MCP is a backend.
5. Confirm the profile must not enable `hdr` and must not import `agents/research-bot`.

Do not call raw `mcp_*` tools. Use `docs_resolve` / `docs_ask` only when a review claim needs an official page.

## Pitfalls

A green `check_profile` does not prove the canvas matches the build.
Collapsed wording that treats a plugin as a tool is a review fail even if the tree validates.
A missing `HONEST-LIMITS.md` is a law-11 fail.

## Verification

Every heuristic has a one-line answer with a file citation.
`check_profile` gaps are listed first.
The review names which of the five §4 patterns are present.
