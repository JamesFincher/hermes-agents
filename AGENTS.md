# Cursor agents — independent Hermes profiles

This repo is a folder of **independent Hermes profile distributions**. Each directory under `agents/` is one specialized profile with its own `HERMES_HOME`. The repo name does not imply a shared runtime.

**Source of truth:** [`docs/PROFILE-PLAYBOOK.md`](docs/PROFILE-PLAYBOOK.md)

Read the playbook before writing files. `docs/WORKFLOW.md` is the PR loop. Do not invent knobs from training data.

## Docs order (every time)

1. Context7 first. Library `/nousresearch/hermes-agent`. Honcho only for the settled memory paragraph. Never print `CONTEXT7_API_KEY`.
2. Then https://hermes-agent.nousresearch.com/llms.txt and the pages the playbook cites.
3. Do not clone NousResearch/hermes-agent or James’s other repos.

## Four surfaces (never collapse)

Skill, Tool, Plugin, and MCP are **four different official objects**. Definitions, load paths, and the one-turn join are in the playbook. Say “the `<name>` plugin registers the `<tool>` tool.”

## Factory rules (summary — details in the playbook)

- One agent per PR. Isolated `HERMES_HOME`. That profile owns its `SOUL.md`, `config.yaml`, skills, MCP, and — if it needs custom tools — its own plugin and toolset. Nothing leaks to the next profile.
- Next agent = follow the playbook under `agents/<name>/`. Write **that** profile’s plugin + skills + MCP only if it needs them. Zero imports from `research-bot`. The next profile starts empty of research-bot’s plugin, tools, and skills.
- There is no factory-root `plugins/` folder. Live process code lives only in `agents/<name>/plugins/<name>/`. Toolset `research-bot` stays on that profile only. Do not copy one profile’s plugin into another. Zero imports from `research-bot`.
- Honcho is settled: `memory.provider: honcho`, unique `aiPeer`, `pinUserPeer: true` (gateway-only). Not `plugins.enabled`.
- If you ship a plugin, claim `plugins` in `distribution_owned` (not in official `DEFAULT_DIST_OWNED`).
- Primary skills stay in profile `skills/`. Do not `ctx.register_skill` the primary library.
- Context7 MCP stays connected when **this** profile’s plugin calls it; facade tools the plugin registers call `ctx.call_mcp`. Skills require those facade names, not `mcp_*`.
- Reserved profile names: `hermes`, `test`, `tmp`, `root`, `sudo`. Do not collide with ouroboros plugin names: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.

## Secrets

Never commit `.env`, `auth.json`, API keys, or `honcho.json` with a real `apiKey`. Installer strip is not `.gitignore`.
