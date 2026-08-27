# research-bot

Independent research-partner profile. Reads source, official docs, and papers. Writes cited findings. Does not implement product code.

This profile ships **its own** plugin at `plugins/research-bot/` (toolset `research-bot`) and research skills in the normal index. The next profile does not inherit this plugin, these tools, or these skills.

Honcho is the memory provider: `memory.provider: honcho`, not a `plugins.enabled` entry.

Kanban description (also in `profile.yaml`):

> Reads source + external docs + papers, writes cited findings, does not implement product code.

## Install (local path)

This repo has no repo-root `distribution.yaml`. GitHub-URL install of `JamesFincher/hermes-agents` will not see this profile. Install the path:

```bash
hermes profile install ./agents/research-bot --alias
```

That copies this directory (including `plugins/research-bot/`) into `~/.hermes/profiles/research-bot/`. This profile is its own `HERMES_HOME`. Official layout: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

Override the local name if `research-bot` already exists:

```bash
hermes profile install ./agents/research-bot --name research-bot-test --alias
```

Reserved names (rejected by the installer): `hermes`, `test`, `tmp`, `root`, `sudo`.

## After install

1. Copy env keys the installer wrote to `.env.EXAMPLE` into the profile `.env` (or export them in the shell). See **env_requires** below.
2. Honcho: copy `honcho.json.example` to the profile `honcho.json` (or merge the `hermes.research-bot` host block into `~/.honcho/config.json`). Put the real API key only in `.env` / `HONCHO_API_KEY` — never commit `honcho.json`. `pinUserPeer: true` is official and **gateway-only**; it does nothing on the CLI.
3. Confirm memory provider:

   ```bash
   hermes memory status
   ```

   Expected: Honcho active. Setup wizard if needed: `hermes memory setup`.
4. Confirm the plugin is enabled (`plugins.enabled: [research-bot]`). Optional doctor (local Hermes, not CI):

   ```bash
   hermes plugins doctor ~/.hermes/profiles/research-bot/plugins/research-bot --ci
   ```
5. Optional kanban text (already shipped in `profile.yaml`):

   ```bash
   hermes profile describe research-bot --text "Reads source + external docs + papers, writes cited findings, does not implement product code."
   ```

## Update

```bash
hermes profile update research-bot
```

`distribution_owned` includes `plugins/` so this profile’s plugin is replaced on update. `config.yaml` is preserved unless you pass `--force-config`. Memories, sessions, `.env`, `auth.json`, and `plugin-data/` are never the install tree.

## env_requires

| Variable | Required | Why |
| --- | --- | --- |
| `HONCHO_API_KEY` | no (Cloud: you still need it) | `memory.provider: honcho`. Honcho Cloud needs this key. Self-hosted uses `baseUrl` in `honcho.json` instead. |
| `CONTEXT7_API_KEY` | no | Header `${env:CONTEXT7_API_KEY}` on the Context7 MCP server. Without it, that server will not authenticate. |
| Model provider key | no (this manifest) | This profile does not pin a model. Use the provider key your Hermes install already needs. |

`HONCHO_API_KEY` is `required: false` because self-hosted Honcho does not use it. If you use Honcho Cloud, set the key anyway — the installer will not block you if it is missing.

## Plugin (this profile only)

The research-bot plugin lives under this profile's `$HERMES_HOME/plugins/research-bot/` after install and does nothing until `plugins.enabled` lists `research-bot`. `plugins.disabled` always wins. Do not put Honcho in `plugins.enabled`. Do not copy this plugin into another profile.

This profile blocks product-code writes from `pre_tool_call`.

Toolset `research-bot` is part of `custom_toolsets.research`. The plugin **registers** these tools:

| Tool | When |
| --- | --- |
| `resolve_library` | Resolve a Context7 library ID (`ctx.call_mcp` → `resolve-library-id`) |
| `docs_query` | Query that library’s docs (`ctx.call_mcp` → `query-docs`) |
| `source_ledger_add` | After retrieving a non-Context7 page |
| `source_ledger_list` | Before writing findings |
| `source_ledger_cite` | Before citing — use only this formatted text |
| `source_ledger_check` | Before asserting a factual claim |

Hooks inject a short contract onto the **user message** (not the system prompt; does not dump skill bodies), block product-code writes, backup-harvest facade tools (not `mcp_*`), and init the ledger on session start.

Settings (`plugins.entries.research-bot.settings`, read via `ctx.get_config`):

- `citation_style`: `apa` | `ieee` | `chicago`

`plugins.entries.research-bot.mcp_allowlist: [context7]` — default-off; no wildcards.

Ledger state lives in `<HERMES_HOME>/plugin-data/research-bot/` via official `plugin_data_dir`. Never next to `plugin.yaml`.

## Context7 MCP

Official Hermes MCP config lives under `mcp_servers` in `config.yaml`. This distribution also ships `mcp.json` because that filename is in the official distribution-owned list.

Both files use documented interpolation (`${env:CONTEXT7_API_KEY}` / `${CONTEXT7_API_KEY}`), not a literal key.

Do not set `tools.include: []` or `enabled: false` — those break `ctx.call_mcp`.

If your installed Hermes only reads `config.yaml` `mcp_servers` (the documented runtime path), you are already covered. If a future installer merges `mcp.json` instead, the same server is there.

## Honcho

- Workspace: `hermes`
- Host block: `hermes.research-bot` (official pattern: `hermes.<profile>`)
- `aiPeer`: `research-bot`
- `recallMode`: `hybrid`
- `writeFrequency`: `async`
- `sessionStrategy`: `per-directory` (documented default). Use `per-repo` only if you want one Honcho session per git root; that is also documented, but this profile often runs from mixed working directories.
- `pinUserPeer`: `true` — official, **gateway-only**. Does not change CLI identity.

Never two writers on this `aiPeer`.

## Toolsets

`custom_toolsets.research` = `web`, `terminal`, `file`, `skills`, `memory`, `session_search`, `research-bot`. `toolsets: [research]` selects that bundle. Built-in names from the official toolsets reference; `research-bot` is the toolset this profile’s plugin registers.

`terminal.cwd` is `"."` (Gateway/cron). CLI uses the launch directory. Backend is `local` — this profile is not a sandbox.

## Skills

Primary skills stay in `skills/` (normal skill index), **not** `plugin:skill`. Each declares `metadata.hermes.requires_toolsets: [research-bot]` so they hide if this profile’s plugin is off.

1. `literature-review` — survey primaries; call `resolve_library` / `docs_query` / `source_ledger_add` / `list` / `cite`.
2. `source-triage` — rank links; call `source_ledger_list` then `source_ledger_add`.
3. `claim-check` — test claims; call `source_ledger_check` then `source_ledger_cite`.

Optional later recipes may live under `../../skills-tap/skills/`. A profile only uses a tap skill after it copies that skill into **its own** `skills/`.

## Cron

None. Official docs: distribution cron is not auto-scheduled. A weekly digest without a delivery target is not justified for this profile.

## Smoke

```bash
hermes profile install ./agents/research-bot --name research-bot-test --alias
research-bot-test chat
# "Name the ledger tools and one write-policy rule. Do not invent a paper."
hermes profile delete research-bot-test --yes
```

Not run in CI (no live Hermes on this repo).
