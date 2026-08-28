---
name: author-profile
description: Playbook steps 5-10 after check_plan is ok. Scaffold, store, hooks, tools, skills, and eval. Stop and use plan-profile if the plan is incomplete.
version: 1.1.0
metadata:
  hermes:
    tags: [Factory, Playbook, Author]
    requires_toolsets: [inception]
    requires_tools: [check_plan, scaffold_profile, check_profile]
    related_skills: [plan-profile, probe-knob, review-profile]
---

# Author a profile

Code after the gate. The plan is the product until `check_plan` is ok.

## When to Use

Use this when `check_plan` is already ok and the user wants `agents/<name>/` written.
Do not use this to start a new job from a one-line sentence (use plan-profile).
Do not use this to write a product app.
Do not use this to share a plugin across profiles.

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/reserved_names.py" '<name>'
```

Call `check_plan` first. If it is not ok, stop and use plan-profile. Then call `scaffold_profile` and `check_profile`.

## Procedure

Call `check_plan` with `name`. If `"ok"` is false, stop. Hand the work to plan-profile. Do not scaffold.

Steps 5-10 produce code only after that gate.

Step 5. Call `scaffold_profile` with `name` and `job` from the plan. It writes a skill-only skeleton that `validate_factory.py` accepts. It is empty of research-bot and inception internals.
6. If the canvas needs durable state, add that profile's store with a `version` field. Do not copy this plugin.
7. Add that profile's hooks before its tools. At least three of intercept-and-distil, fence, free output, ledger, governor.
8. Register that profile's tools. Static guidance goes in a prompt section. The volatile digest has a plugin cap.
9. Write disjoint skills. Gate them on **that** profile's toolset. Invoke scripts with `${HERMES_SKILL_DIR}`.
10. Freeze eval tasks. Run `check_profile` on `agents/<name>`. Write `HONEST-LIMITS.md`. Regenerate the deep-dive from shipped files.

Do not call raw `mcp_*` tools. Docs work belongs to plan-profile. The inception plugin registers `check_plan` and `scaffold_profile`. There is no `moa` toolset.

## Pitfalls

Skipping `check_plan` fails the fence. A job line is not enough.
A reserved name (`hermes`, `test`, `tmp`, `root`, `sudo`) fails the fence.
`forge` and the other ouroboros ids are plugin-name collisions.
Enabling `hdr` on the new profile is a fail.
A repo-root `distribution.yaml` is [UNV] and must not ship.
Do not invent `hermes plugins doctor`.

## Verification

`check_plan` was ok before scaffold.
`check_profile` returns `"ok": true`.
`python3 scripts/validate_factory.py` still passes.
The new tree has zero imports from `agents/research-bot`.
The canvas matches the files.
