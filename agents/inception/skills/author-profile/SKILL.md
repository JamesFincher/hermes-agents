---
name: author-profile
description: Run the playbook loop. Steps 0-4 write docs. Steps 5-10 write code. Use when the user wants a new isolated Hermes profile.
version: 1.0.0
metadata:
  hermes:
    tags: [Factory, Playbook, Author]
    requires_toolsets: [inception]
    requires_tools: [docs_resolve, docs_ask, probe_knob, scaffold_profile, check_profile]
    related_skills: [probe-knob, review-profile]
---

# Author a profile

Turn a job into one `agents/<name>/` distribution. Docs first. Code second.

## When to Use

Use this when the user asks for a new Hermes profile, a factory run, or "follow the playbook."
Do not use this to write a product app.
Do not use this to share a plugin across profiles.

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/reserved_names.py" '<name>'
```

Then call `docs_resolve`, `docs_ask`, `probe_knob`, `scaffold_profile`, and `check_profile` in that order.

## Procedure

Steps 0-4 produce documents. Do not write `agents/<name>/` yet.

Step 0. Call `docs_resolve` with library_name `Hermes Agent` and query `configuration toolsets hooks plugins skills`. Then call `docs_ask` on `/nousresearch/hermes-agent` for each surface the job needs. For memory only, resolve `/plastic-labs/honcho`.
1. Study the incumbent from published docs. Map 5-10 mechanisms to Hermes surfaces.
2. Write the canvas using playbook §6. One job. One scarce resource. One store schema.
3. If this updates an existing profile, write a gap register. Do not propose fixes in that pass.
4. Write `docs/profiles/<name>-spec.md`. Tag every platform claim `[DOC]`, `[INF]`, or `[UNV]`.

Call `probe_knob` once per §5 knob before that knob appears in `config.yaml`. `[UNV]` must set `code_depends` false.

Steps 5-10 produce code.

Step 5. Call `scaffold_profile` with `name` and `job`. It writes a skill-only skeleton that `validate_factory.py` accepts. It is empty of research-bot and inception internals.
6. If the canvas needs durable state, add that profile's store with a `version` field. Do not copy this plugin.
7. Add that profile's hooks before its tools. At least three of intercept-and-distil, fence, free output, ledger, governor.
8. Register that profile's tools. Static guidance goes in a prompt section. The volatile digest has a plugin cap.
9. Write disjoint skills. Gate them on **that** profile's toolset. Invoke scripts with `${HERMES_SKILL_DIR}`.
10. Freeze eval tasks. Run `check_profile` on `agents/<name>`. Write `HONEST-LIMITS.md`. Regenerate the deep-dive from shipped files.

Do not call raw `mcp_*` tools. The inception plugin registers `docs_resolve` and `docs_ask`. Official pages may use `web_search` and `web_extract` only after Context7 misses. There is no `moa` toolset.

## Pitfalls

A reserved name (`hermes`, `test`, `tmp`, `root`, `sudo`) fails the fence.
`forge` and the other ouroboros ids are plugin-name collisions.
Enabling `hdr` on the new profile is a fail.
A repo-root `distribution.yaml` is [UNV] and must not ship.
Do not invent `hermes plugins doctor`.

## Verification

`check_profile` returns `"ok": true`.
`python3 scripts/validate_factory.py` still passes.
The new tree has zero imports from `agents/research-bot`.
The canvas matches the files.
