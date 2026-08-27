# Workflow

Herbert points Cursor here. One loop, one PR.

## Intake

1. Read the request. Identify **one** unit of work:
   - one new **agent** (the whole distribution: SOUL, config, Honcho, skills, and any plugin that agent needs), **or**
   - one shared **skill recipe** (`skills-tap/`), **or**
   - one extracted **shared plugin** once two agents already need the same host primitive.
2. Read `AGENTS.md` — especially **Product model** and **How plugins actually load**. Do not start from memory of Hermes knobs.
3. If the request spans two agents, split it. Do not write both.

**Never ask "plugin or skills first."** Skills are recipes. Plugins are process code. They are the same product, different layers. Honcho is already the memory plugin (`memory.provider: honcho`).

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

- New agent: `agents/<name>/` with `distribution.yaml` at that directory's root. Fill the distribution as one product. If the agent needs a host capability (custom tool, hook, middleware), ship `plugins/<id>/` **and** list it in that profile's `plugins.enabled`. Claim `plugins` in `distribution_owned` (it is not in the official default owned set). Do not invent a dummy plugin.
- Enable list is per profile. `plugins.disabled` always wins. Honcho is not an `enabled` entry.
- Per-agent plugin: `agents/<name>/plugins/<name>/`, enabled only on that profile.
- Shared plugin (only after two agents copy the same primitive): factory `plugins/<shared>/`, copied into each consumer's `agents/<consumer>/plugins/<shared>/`, each consumer enables `<shared>` on **its** `config.yaml`.
- Skill recipes stay in `agents/<name>/skills/` (or `skills-tap/skills/` when shared). They are not a substitute for process code. Do not make the primary library `plugin:skill`. If a skill needs a plugin toolset, declare `requires_toolsets` / `requires_tools`.
- Cron / blueprint: suggestion only. Official docs: distribution cron is **not** auto-scheduled.

Target `~/.hermes`. Do not vendor Gengar or fork Ouroboros.

## PR

- Title names the single unit (`research-bot`, `skills-tap/<slug>`, `plugins/<shared>`, …).
- Body lists Context7 library IDs + official URLs actually used, and any fallback.
- No secrets. No drive-by refactors.

## Install smoke

Not required in CI (no live Hermes here). On a machine with Hermes:

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
# quoted smoke prompt that exercises SOUL + the process/recipe pair
hermes profile info <name>-test
hermes profile delete <name>-test --yes
```

GitHub-URL install of this repo will **not** install the army. There is no repo-root `distribution.yaml`. Install a path:

```bash
hermes profile install ./agents/<name> --alias
```
