# Workflow

Herbert points Cursor here. One loop, one PR.

## Intake

1. Read the request. Identify **one** unit of work:
   - one new **agent** (the whole distribution), **or**
   - one **skill recipe** (`agents/<name>/skills/` or `skills-tap/`), **or**
   - one **host capability** on `army-runtime` (plus `requires_tools` on the skill that needs it), **or**
   - one **per-agent plugin** only when a capability must not leak.
2. Read `AGENTS.md` — especially **Join layer**. Do not start from memory of Hermes knobs.
3. If the request spans two agents, split it. Do not write both.

Do not ask "plugin or skills first." Skills are recipes in the normal index. `army-runtime` is shared process code. Honcho is `memory.provider: honcho`.

**New skill that needs a new host capability → add the tool to army-runtime, declare `requires_tools` / `requires_toolsets: [army]` on the skill, keep `plugins.enabled: [army-runtime]`.**

## Context7

For every Hermes / Honcho / library question:

1. Query Context7 (Context7-API) with the official library IDs:
   - `/nousresearch/hermes-agent`
   - `/plastic-labs/honcho`
   - `/llmstxt/hermes-agent_nousresearch_llms_txt` and `/websites/honcho_dev_v3` when needed
2. Then open the official pages from https://hermes-agent.nousresearch.com/llms.txt.
3. Cite the hit in the PR. If Context7 is unavailable, say so and use llms.txt + the indexed pages.

Never invent a `config.yaml` / `honcho.json` / `distribution.yaml` / `plugin.yaml` / `SKILL.md` key.

## Implement

- New agent: `agents/<name>/` with `distribution.yaml` at that directory's root. Copy `plugins/army-runtime/` into `agents/<name>/plugins/army-runtime/`. `plugins.enabled: [army-runtime]`. Claim `plugins` in `distribution_owned`.
- Skills stay in `agents/<name>/skills/` or `skills-tap/skills/<slug>/SKILL.md`. They must appear in the normal skill index. Do **not** `ctx.register_skill` / `plugin:skill` the primary library.
- New host capability: edit factory `plugins/army-runtime/`, recopy into every consumer, declare `requires_tools` on the skill.
- Per-agent plugin: only when the capability must not leak to other profiles.
- Cron / blueprint: suggestion only. Official docs: distribution cron is **not** auto-scheduled.

Target `~/.hermes`. Do not vendor Gengar or fork Ouroboros.

## PR

- Title names the single unit (`research-bot`, `skills-tap/<slug>`, `army-runtime`, …).
- Body lists Context7 library IDs + official URLs actually used, and any fallback.
- No secrets. No drive-by refactors.

## Install smoke

Not required in CI (no live Hermes here). On a machine with Hermes:

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
# quoted smoke prompt that exercises SOUL + an army-backed skill
hermes profile info <name>-test
hermes profile delete <name>-test --yes
```

GitHub-URL install of this repo will **not** install the army. There is no repo-root `distribution.yaml`. Install a path:

```bash
hermes profile install ./agents/<name> --alias
```
