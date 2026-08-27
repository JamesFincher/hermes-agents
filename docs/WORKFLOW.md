# Workflow

Herbert points Cursor here. One loop, one PR.

## Intake

1. Read the request. Identify **one** unit of work: one new agent (plugin + skills), **or** one shared skill recipe, **or** one host capability on **that** agent's plugin.
2. Read `AGENTS.md`. Do not start from memory of Hermes knobs.
3. If the request spans two agents, split it. Do not write both.

## Context7

For every Hermes / Honcho / library question:

1. Query Context7 (Context7-API) with the official library IDs:
   - `/nousresearch/hermes-agent`
   - `/plastic-labs/honcho`
   - `/llmstxt/hermes-agent_nousresearch_llms_txt` and `/websites/honcho_dev_v3` when needed
2. Then open the official pages from https://hermes-agent.nousresearch.com/llms.txt.
3. Cite the hit in the PR. If Context7 is unavailable, say so and use llms.txt + the indexed pages.

Never invent a `config.yaml` / `honcho.json` / `distribution.yaml` / `SKILL.md` key.

## Implement

- New agent: `agents/<name>/` with `distribution.yaml` at that directory's root, plus `plugins/<name>/` enabled only on that profile. Skills stay in `agents/<name>/skills/` and `requires_toolsets: [<name>]`.
- Shared skill recipe: `skills-tap/skills/<slug>/SKILL.md` only. Do not copy it into every agent. Do not make the primary library `plugin:skill`.
- New host capability for one agent: add it to **that** agent's plugin. Do not start a shared army-runtime.
- Cron / blueprint: suggestion only. Official docs: distribution cron is **not** auto-scheduled.

Target `~/.hermes`. Do not vendor Gengar or fork Ouroboros.

## PR

- Title names the single unit (`research-bot`, `skills-tap/<slug>`, …).
- Body lists Context7 library IDs + official URLs actually used, and any fallback.
- No secrets. No drive-by refactors.

## Install smoke

Not required in CI (no live Hermes here). On a machine with Hermes:

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
# quoted smoke prompt that exercises SOUL + one skill
hermes profile info <name>-test
hermes profile delete <name>-test --yes
```

GitHub-URL install of this repo will **not** install the army. There is no repo-root `distribution.yaml`. Install a path:

```bash
hermes profile install ./agents/<name> --alias
```
