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

## Join layer (skills + plugins)

A profile distribution **carries** SOUL, config, skills, cron, MCP, and plugins. Official: https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions

Do not frame this as "plugin or skills first." They are different layers of the same product.

| Layer | What it is | Where it lives |
| --- | --- | --- |
| **Skills** | Recipes. Appear in the normal `<available_skills>` index. | `agents/<name>/skills/` and repo-root `skills-tap/skills/<slug>/SKILL.md` |
| **army-runtime** | Shared process code. Toolset `army`. | Factory `plugins/army-runtime/` copied into each `agents/<name>/plugins/army-runtime/` |
| **Honcho** | Exclusive **memory provider** plugin. | `memory.provider: honcho` — **not** `plugins.enabled` |
| **Per-agent plugin** | Only when a capability **must not leak**. | `agents/<name>/plugins/<name>/` + that name in that profile's `plugins.enabled` |

**Do not** put the primary skill library inside a plugin (`ctx.register_skill` / `plugin:skill`). Those loads are hidden, read-only, and opt-in — wrong for "any custom skill."

**New skill that needs a new host capability** → add the tool to `army-runtime`, declare `requires_toolsets: [army]` and/or `requires_tools` on the skill, keep `plugins.enabled: [army-runtime]`. Per-agent plugin only when the capability must not leak.

## How plugins actually load

Official: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins

- Each profile is its own `$HERMES_HOME` (`~/.hermes/profiles/<name>/`).
- General plugins live at `$HERMES_HOME/plugins/<name>/`. After `hermes profile install ./agents/<name>`, that is `agents/<name>/plugins/<name>/` copied into the profile.
- They **do nothing** until that profile's `config.yaml` lists them in `plugins.enabled`.
- Every agent in this factory lists `army-runtime` in `plugins.enabled`. Do not put Honcho there.
- `plugins.disabled` is a deny-list. A name in `disabled` never loads, even if it is also in `enabled`.
- Default `distribution_owned` is `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `distribution.yaml`. **`plugins/` is not in the default set.** Claim `plugins` or updates will not replace army-runtime. Setting `distribution_owned` replaces the default list — include the defaults you still want plus `plugins`.
- Plugin state belongs in profile-scoped `plugin-data/` (`plugin_data_dir`), never the install tree.

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
| `agents/<name>/` | One distribution. Install this path. |
| `agents/<name>/skills/` | That agent's recipes. Normal skill index. |
| `agents/<name>/plugins/army-runtime/` | Copy of the shared process layer (must match factory source). |
| `plugins/army-runtime/` | Factory source of truth for the shared plugin. |
| `skills-tap/skills/` | Shared recipes later (`hermes skills tap add`). Default tap path is `skills/`; after `tap add`, set `"path": "skills-tap/skills/"` in `~/.hermes/skills/.hub/taps.json`. |
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
3. Fill the **whole distribution**:
   - `distribution.yaml` — `name`, `version`, `description`, `author`, `env_requires` (honest `required` flags), `hermes_requires` only if you can justify a floor. Claim `plugins` in `distribution_owned`.
   - `SOUL.md` — identity / tone only. Slot #1. No project paths.
   - `profile.yaml` — kanban routing (`description`, `description_auto: false`).
   - `config.yaml` — cited knobs only. `memory.provider: honcho`. `plugins.enabled: [army-runtime]` (plus a per-agent plugin only if a capability must not leak). Add toolset `army` to `custom_toolsets`. Set `plugins.entries.army-runtime.settings` as needed (`write_policy: research` only on research profiles).
   - Copy `plugins/army-runtime/` → `agents/<name>/plugins/army-runtime/` (keep identical). If you add a host capability, edit the factory source first, then recopy.
   - `honcho.json.example` — shared `workspace`, unique `aiPeer`, host `hermes.<name>`. No real `apiKey`.
   - `mcp.json` / `config.yaml` `mcp_servers` — only if headers can use `${env:VAR}` / `${VAR}`.
   - `skills/` — 1–3 high-leverage recipes in the **normal index**. `metadata.hermes.requires_toolsets: [army]` and `requires_tools` for army tools they need. Shared-later recipes go in `skills-tap/skills/`.
4. Reserved names (rejected at install): `hermes`, `test`, `tmp`, `root`, `sudo`.
5. Update the root README agent table.
6. Smoke (local Hermes, not CI):

```bash
hermes profile install ./agents/<name> --name <name>-test --alias
<name>-test chat
# quoted smoke prompt that exercises SOUL + an army-backed skill
hermes profile delete <name>-test --yes
```

Do not require a live Hermes in CI. Structure checks in `.github/workflows/validate.yml` are enough.

## Honcho host block

Official mapping: host key `hermes` → default profile; `hermes.<name>` for others. `aiPeer` is one per Hermes profile. Workspace is shared. Never two writers on one `aiPeer`.
