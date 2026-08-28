---
name: plan-profile
description: Playbook steps 0-4 only. Investigate tools, skills, MCPs, and plugins. Write canvas and spec. End when check_plan is ok. Do not scaffold.
version: 1.1.0
metadata:
  hermes:
    tags: [Factory, Playbook, Plan]
    requires_toolsets: [inception]
    requires_tools: [docs_resolve, docs_ask, probe_knob, plan_start, investigate_surface, write_canvas, write_spec, check_plan]
    related_skills: [author-profile, probe-knob, review-profile]
---

# Plan a profile

Docs first. Code later. This skill stops at a complete plan.

## When to Use

Use this when the user asks for a new Hermes profile, a factory run, or "follow the playbook," and no complete plan exists yet.
Do not use this to write `agents/<name>/` (use author-profile after `check_plan` is ok).
Do not use this to review a finished tree (use review-profile).

## Quick Reference

```bash
python "${HERMES_SKILL_DIR}/scripts/tracks.py"
python "${HERMES_SKILL_DIR}/../author-profile/scripts/reserved_names.py" '<name>'
```

Then call `plan_start`, `docs_resolve`, `docs_ask`, `investigate_surface`, `probe_knob`, `write_canvas`, `write_spec`, and `check_plan`.
Do not call `scaffold_profile` from this skill.

## Procedure

Steps 0-4 produce documents. Do not write `agents/<name>/`.

Step 0. Call `plan_start` with `name`, `job`, `incumbent`, and `axis`. Call `docs_resolve` with library_name `Hermes Agent`. Then call `docs_ask` on `/nousresearch/hermes-agent` for each official topic: configuration, toolsets, event hooks, plugins, adding-tools, creating-skills, MCP, prompt assembly, and delegation. For memory only, resolve `/plastic-labs/honcho`. Never invent knobs.
1. Study the incumbent from published docs. Map 5-10 mechanisms to Hermes surfaces.
2. Walk four investigation tracks. Call `investigate_surface` at least once for `tool`, `skill`, `mcp`, and `plugin`. Use the playbook §3 decision tree for `mapping`. If kind is `tool`, answer q1, q2, and q3. MCP or plugin may be `reject` with a reason. Also walk `hook` and `config` when the job needs them.
3. Call `probe_knob` for every playbook §5 context-economics knob. Pass `name` so the row attaches to this plan. `[UNV]` must set `code_depends` false.
4. Call `write_canvas` with all 12 playbook §6 sections filled. Then call `write_spec` at counsel and HDR depth: verdict, incumbent map, inventions, nine surfaces, plugin file map, full tool schemas, hook table, data schemas, skill list, MCP list or explicit none, delegation, token economics, failure ladder, eval (8+ tasks, 2 adversarial), P1-P10 acceptance, honest limits. Tag every platform claim `[DOC]`, `[INF]`, or `[UNV]`.

Call `check_plan` with `name`. If `"ok"` is false, close the gaps and call it again. This skill ends when `check_plan` is ok.

Do not call raw `mcp_*` tools. The inception plugin registers `docs_resolve` and `docs_ask`. Official pages may use `web_search` and `web_extract` only after Context7 misses. There is no `moa` toolset.

## Pitfalls

A one-line job is not a plan. `scaffold_profile` will fail until `check_plan` is ok.
Prompted "docs first" will be dropped at turn 40. The fence is the gate.
Do not copy another profile's plugin. Do not import `hdr`.
A reserved name (`hermes`, `test`, `tmp`, `root`, `sudo`) fails. `forge` is reserved.
Do not invent `hermes plugins doctor`. Do not add a repo-root `distribution.yaml`.

## Verification

`check_plan` returns `"ok": true`.
The four tracks each have a row.
`docs/profiles/<name>-canvas.md` has 12 filled sections.
`docs/profiles/<name>-spec.md` is not a stub and names plugin, tool, skill, and MCP.
