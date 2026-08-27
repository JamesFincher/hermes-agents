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

## Product model (do not invert this)

A profile distribution **carries** SOUL, config, skills, cron, MCP, and plugins. Official: https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions

| Layer | What it is | What it is not |
| --- | --- | --- |
| **Skills** | Recipes. `SKILL.md` tells the model when and how. | Not host process code. |
| **General plugins** | Process code: tools, hooks, middleware. `plugin.yaml` + `register(ctx)`. | Not optional garnish on top of skills. |
| **Honcho** | Already a plugin: exclusive **memory provider**. Select with `memory.provider: honcho`. | Not a `plugins.enabled` entry. |

Never ask "plugin or skills first." Design the recipe and the process code as one agent. If the recipe needs a host capability built-ins cannot guarantee (custom tool, hook, middleware), that capability **is** the plugin and ships in the same distribution. If built-ins + Honcho are enough, do **not** invent a dummy plugin.

## How plugins actually load

Official: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins

- Each profile is its own `$HERMES_HOME` (`~/.hermes/profiles/<name>/`).
- General/standalone plugins live at `$HERMES_HOME/plugins/<name>/` (that profile home). After `hermes profile install ./agents/<name>`, that is `agents/<name>/plugins/<name>/` copied into the profile.
- They **do nothing** until that profile's `config.yaml` lists them in `plugins.enabled`.
- `plugins.disabled` is a deny-list. A name in `disabled` never loads, even if it is also in `enabled`.
- Default `distribution_owned` is `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `distribution.yaml`. **`plugins/` is not in the default set.** If the agent ships plugins, claim `plugins` in `distribution_owned` or updates will not replace them. Setting `distribution_owned` replaces the default list — include the defaults you still want plus `plugins` plus anything else you ship.
- Plugin state belongs in profile-scoped `plugin-data/` (`plugin_data_dir`), never the install tree.

## Shared vs per-agent plugins (next agent)

Each profile is an isolated home. "Shared" does **not** mean one global runtime all profiles load automatically.

| Kind | Where the code lives in this factory | How the next agent enables it |
| --- | --- | --- |
| **Per-agent** | `agents/<name>/plugins/<name>/` | That profile only: `plugins.enabled` includes `<name>`. Do not enable it on other agents. |
| **Shared** (extract later) | Factory source `plugins/<shared>/`, **copied/owned** by each consumer as `agents/<consumer>/plugins/<shared>/` | Each consumer lists `<shared>` in **its own** `plugins.enabled`. Agents that do not need it omit it. Claim `plugins` on every consumer that ships the directory. |

Do not build a shared army-runtime first. If two later agents copy the same host primitive, extract then into `plugins/<shared>/` and enable it per profile as above.

Do not collide with ouroboros names: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.

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
| `agents/<name>/` | One distribution. Install this path. Carries SOUL, config, skills, plugins, MCP. |
| `agents/<name>/plugins/<id>/` | Process code owned by that distribution (`$HERMES_HOME/plugins/<id>/` after install). |
| `plugins/` | Factory source for **extracted shared** plugins later. Not an army-runtime. See `plugins/README.md`. |
| `skills-tap/skills/` | Shared **recipes** later (`hermes skills tap add`). Default tap path is `skills/`; this factory uses `skills-tap/skills/` so agent-local skills stay out of the tap. After `tap add`, set `"path": "skills-tap/skills/"` in `~/.hermes/skills/.hub/taps.json`. |
| `AGENTS.md` + `.cursor/rules/` | Cursor workflow. Not Hermes `SOUL.md`. |

## One agent per PR

Tight. Recreatable. No drive-by refactors of other profiles.

Never two writers on one profile. Honcho is **shared memory**: one workspace, unique `aiPeer` per profile, host block `hermes.<name>`.

## Never invent knobs

Every `config.yaml`, `distribution.yaml`, `honcho.json*`, `mcp.json`, `plugin.yaml`, and `SKILL.md` key must be citeable from Context7 or official docs. If you cannot cite it, leave it out.

## Secrets

Never commit `.env`, `auth.json`, API keys, `memories/`, `sessions/`, `state.db*`, or `honcho.json` with a real `apiKey`.

The installer **strips** those paths at install time. That is **not** a substitute for `.gitignore`. Authors must keep secrets out of git.

Ship `honcho.json.example` only. After install, the operator copies it to the profile's `honcho.json` or `~/.honcho/config.json` and fills `apiKey` locally (or uses `HONCHO_API_KEY` / `hermes memory setup`).

## Cron and other repos

- Cron jobs in a distribution are **not auto-scheduled** (official profile-distributions security note). Blueprints become `/suggestions`. Do not add `cron/` unless a suggested blueprint is justified in the PR.
- Do **not** vendor JamesFincher/gengar (engine, `~/.gengar`) or rewrite JamesFincher/hermes-ouroboros (plugin pack, Apache-2.0, `~/.hermes/plugins`). Depend or leave a hook in `plugins/README.md`.
- Target stock Hermes `~/.hermes`, not Gengar.

## How to add agent N+1

1. Context7 + official docs for any knob you will set.
2. Copy `agents/research-bot/` to `agents/<name>/` **or** follow the checklist below on a fresh directory.
3. Fill the **whole distribution** (not skills first, not plugin first):
   - `distribution.yaml` — `name`, `version`, `description`, `author`, `env_requires` (honest `required` flags), `hermes_requires` only if you can justify a floor. If you ship plugins, claim `plugins` in `distribution_owned` (and keep the other owned paths you still want).
   - `SOUL.md` — identity / tone only. Slot #1. No project paths.
   - `profile.yaml` — kanban routing description (`description`, `description_auto: false`).
   - `config.yaml` — only cited knobs. Honcho: `memory.provider: honcho` (the memory plugin). General plugins: `plugins.enabled` lists every standalone plugin this profile should load. Do not put Honcho there.
   - **Process code, when required:** `plugins/<id>/` with a real `plugin.yaml` + `register(ctx)`. Enable each shipped `<id>` on this profile. Add plugin toolsets to `custom_toolsets` so the tools are actually on. Per-agent default: `plugins/<name>/` enabled only here. Shared: copy `plugins/<shared>/` into this agent and add `<shared>` to this profile's `plugins.enabled`.
   - `honcho.json.example` — shared `workspace`, unique `aiPeer`, host `hermes.<name>`. No real `apiKey`.
   - `mcp.json` / `config.yaml` `mcp_servers` — only if headers can use `${env:VAR}` / `${VAR}`.
   - **Recipes:** `skills/` — 1–3 high-leverage skills with valid `SKILL.md` frontmatter (`name`, `description`, `metadata.hermes`). Stay in the normal skill index (not `plugin:skill`). If they depend on a plugin toolset, set `requires_toolsets` / `requires_tools` so they hide when that plugin is off. Shared-later recipes go in `skills-tap/skills/`.
4. Reserved names (rejected at install): `hermes`, `test`, `tmp`, `root`, `sudo`.
5. Update the root README agent table.
6. Smoke (local Hermes, not CI):

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
# quoted smoke prompt that exercises SOUL + the process/recipe pair
hermes profile delete <name>-test --yes
```

Do not require a live Hermes in CI. Structure checks in `.github/workflows/validate.yml` are enough.

## Honcho host block

Official mapping: host key `hermes` → default profile; `hermes.<name>` for others. `aiPeer` is one per Hermes profile. Workspace is shared. Never two writers on one `aiPeer`.
