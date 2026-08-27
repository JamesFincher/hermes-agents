# Workflow

Herbert points Cursor here. One loop, one PR.

**Source of truth:** [`PROFILE-PLAYBOOK.md`](PROFILE-PLAYBOOK.md)

The playbook teaches how to generate **one independent specialized Hermes profile**. Follow it. Do not start from another profile’s plugin or skills.

## Intake

1. Read the request. Identify **one** unit: one new agent, or one skill recipe, or one change to **that** agent’s plugin / MCP.
2. Read the playbook — especially the four surfaces and the footprint ladder. Do not start from memory of Hermes knobs.
3. If the request spans two agents, split it.

## Context7

For every Hermes / Honcho / library question:

1. Query Context7 with `/nousresearch/hermes-agent` (Honcho only for the settled memory paragraph).
2. Then open the official pages from https://hermes-agent.nousresearch.com/llms.txt.
3. Cite the hit in the PR. If Context7 is unavailable, say so and use llms.txt.

Never invent a `config.yaml` / `honcho.json` / `distribution.yaml` / `plugin.yaml` / `SKILL.md` key.

## Implement

Follow the playbook checklist. Short version:

- New agent: `agents/<name>/` with `distribution.yaml` at that directory’s root. That agent’s own `plugins/<name>/` **only if** it needs process code. `plugins.enabled: [<name>]`. Claim `plugins` in `distribution_owned`.
- Skills in `agents/<name>/skills/`. Normal index. `requires_toolsets` / `requires_tools` of tools **this** plugin registers. Do not require another profile’s toolset.
- No factory-root plugin package. Zero imports from another agent’s plugin. The next profile starts empty of `research-bot`’s plugin, tools, and skills.
- Cron / blueprint: suggestion only. Official: distribution cron is not auto-scheduled.

Local doctor (not CI):

```bash
hermes plugins doctor ~/.hermes/profiles/<name>/plugins/<name> --ci
```

## PR

- Title names the single unit.
- Body lists Context7 library IDs + official URLs actually used, and any UNVERIFIED flags.
- No secrets. No drive-by refactors.

## Install smoke

Not required in CI. On a machine with Hermes:

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
hermes profile delete <name>-test --yes
```

GitHub-URL install of this repo will **not** install a profile. There is no repo-root `distribution.yaml`. Install `./agents/<name>`.
