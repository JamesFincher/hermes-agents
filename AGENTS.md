# Cursor agents — Hermes factory

This repo is a factory for Hermes Agent **profile distributions**. Each directory under `agents/` is one installable profile. Herbert (James's director) will ask you to add agents one by one.

Read `docs/WORKFLOW.md` before you write files.

## Docs order (do this every time)

1. **Context7 first.** Resolve + query. Do not invent knobs from training data.
   - Hermes Agent: `/nousresearch/hermes-agent`
   - Honcho: `/plastic-labs/honcho`
   - Also useful: `/llmstxt/hermes-agent_nousresearch_llms_txt`, `/websites/honcho_dev_v3`
   - James's paid Context7 is connected as **Context7-API**. Use it.
   - `CONTEXT7_API_KEY` exists as a GitHub Actions secret on this repo. Never print, log, or commit it. Do not put any API key in files.
2. **Then official Hermes LLM entry points:**
   - https://hermes-agent.nousresearch.com/llms.txt
   - https://hermes-agent.nousresearch.com/llms-full.txt
   - The pages they index — especially profile-distributions, profiles, configuration, creating-skills, plugins, honcho, memory-providers, personality, bot-mode, kanban, mcp, cron.
3. **Do not clone** NousResearch/hermes-agent or any of James's other repos. Official docs / Context7 / GitHub raw/API only.

If Context7 is down, use the llms.txt pages and say so in the PR.

## Layout (why it is this way)

Official docs do **not** prescribe a monorepo. They **do** allow:

```bash
hermes profile install ./path
```

when `distribution.yaml` is at that path's root.

```bash
hermes profile install github.com/owner/repo
```

only sees **repo-root** `distribution.yaml`. This factory therefore uses **per-agent directories**. We do not pretend one GitHub URL installs the whole army.

| Path | Role |
| --- | --- |
| `agents/<name>/` | One distribution. Install this path. |
| `skills-tap/skills/` | Shared tap later (`hermes skills tap add`). Default tap path is `skills/`; this factory uses `skills-tap/skills/` so agent-local skills stay out of the tap. After `tap add`, set `"path": "skills-tap/skills/"` in `~/.hermes/skills/.hub/taps.json`. |
| `plugins/` | Factory hook only. Empty until a plugin is actually shipped. Plugins are opt-in. |
| `AGENTS.md` + `.cursor/rules/` | Cursor workflow. Not Hermes `SOUL.md`. |

## One agent per PR

Tight. Recreatable. No drive-by refactors of other profiles.

Never two writers on one profile. Honcho is **shared memory**: one workspace, unique `aiPeer` per profile, host block `hermes.<name>`.

## Never invent knobs

Every `config.yaml`, `distribution.yaml`, `honcho.json*`, `mcp.json`, and `SKILL.md` key must be citeable from Context7 or official docs. If you cannot cite it, leave it out.

## Secrets

Never commit `.env`, `auth.json`, API keys, `memories/`, `sessions/`, `state.db*`, or `honcho.json` with a real `apiKey`.

The installer **strips** those paths at install time. That is **not** a substitute for `.gitignore`. Authors must keep secrets out of git.

Ship `honcho.json.example` only. After install, the operator copies it to the profile's `honcho.json` or `~/.honcho/config.json` and fills `apiKey` locally (or uses `HONCHO_API_KEY` / `hermes memory setup`).

## Plugins, cron, other repos

- Plugins default **disabled**. Set `plugins.enabled` only if this PR ships that plugin.
- Cron jobs in a distribution are **not auto-scheduled** (official profile-distributions security note). Blueprints become `/suggestions`. Do not add `cron/` unless a suggested blueprint is justified in the PR.
- Do **not** vendor JamesFincher/gengar (engine, `~/.gengar`) or rewrite JamesFincher/hermes-ouroboros (plugin pack, Apache-2.0, `~/.hermes/plugins`). Depend or leave a hook in `plugins/README.md`.
- Target stock Hermes `~/.hermes`, not Gengar.

## How to add agent N+1

1. Context7 + official docs for any knob you will set.
2. Copy `agents/research-bot/` to `agents/<name>/` **or** follow the checklist below on a fresh directory.
3. Fill, in this order:
   - `distribution.yaml` — `name`, `version`, `description`, `author`, `env_requires` (honest `required` flags), `hermes_requires` only if you can justify a floor.
   - `SOUL.md` — identity / tone only. Slot #1. No project paths.
   - `profile.yaml` — kanban routing description (`description`, `description_auto: false`).
   - `config.yaml` — only cited knobs. Honcho: `memory.provider: honcho`.
   - `honcho.json.example` — shared `workspace`, unique `aiPeer`, host `hermes.<name>`. No real `apiKey`.
   - `mcp.json` / `config.yaml` `mcp_servers` — only if headers can use `${env:VAR}` / `${VAR}`.
   - `skills/` — 1–3 high-leverage skills with valid `SKILL.md` frontmatter (`name`, `description`, `metadata.hermes`). Shared-later skills go in `skills-tap/skills/`, not copied into every agent.
4. Reserved names (rejected at install): `hermes`, `test`, `tmp`, `root`, `sudo`.
5. Update the root README agent table.
6. Smoke (local Hermes, not CI):

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
# quoted smoke prompt, e.g.:
# "Name two primary-source rules from your SOUL. Do not invent a paper."
hermes profile delete <name>-test --yes
```

Do not require a live Hermes in CI. Structure checks in `.github/workflows/validate.yml` are enough.

## Honcho host block

Official mapping: host key `hermes` → default profile; `hermes.<name>` for others. `aiPeer` is one per Hermes profile. Workspace is shared. Never two writers on one `aiPeer`.
