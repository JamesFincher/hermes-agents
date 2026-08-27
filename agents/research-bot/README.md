# research-bot

Research partner profile. Reads source, official docs, and papers. Writes cited findings. Does not implement product code.

Kanban description (also in `profile.yaml`):

> Reads source + external docs + papers, writes cited findings, does not implement product code.

## Install (local path)

This factory has no repo-root `distribution.yaml`. GitHub-URL install of `JamesFincher/hermes-agents` will not see this profile. Install the path:

```bash
hermes profile install ./agents/research-bot --alias
```

Override the local name if `research-bot` already exists:

```bash
hermes profile install ./agents/research-bot --name research-bot-test --alias
```

Reserved names (rejected by the installer): `hermes`, `test`, `tmp`, `root`, `sudo`.

## After install

1. Copy env keys the installer wrote to `.env.EXAMPLE` into the profile `.env` (or export them in the shell). See **env_requires** below.
2. Honcho: copy `honcho.json.example` to the profile `honcho.json` (or merge the `hermes.research-bot` host block into `~/.honcho/config.json`). Put the real API key only in `.env` / `HONCHO_API_KEY` — never commit `honcho.json`.
3. Confirm memory provider:

   ```bash
   hermes memory status
   ```

   Expected: Honcho active. Setup wizard if needed: `hermes memory setup`.
4. Optional kanban text (already shipped in `profile.yaml`):

   ```bash
   hermes profile describe research-bot --text "Reads source + external docs + papers, writes cited findings, does not implement product code."
   ```

## Update

```bash
hermes profile update research-bot
```

Distribution-owned paths are replaced (`SOUL.md`, `mcp.json`, `skills/`, `distribution.yaml`). `config.yaml` is preserved unless you pass `--force-config`. Memories, sessions, `.env`, and `auth.json` are never touched.

## env_requires

| Variable | Required | Why |
| --- | --- | --- |
| `HONCHO_API_KEY` | no (Cloud: you still need it) | `memory.provider: honcho`. Honcho Cloud needs this key. Self-hosted uses `baseUrl` in `honcho.json` instead. |
| `CONTEXT7_API_KEY` | no | Header `${env:CONTEXT7_API_KEY}` on the Context7 MCP server. Without it, that server will not authenticate. |
| Model provider key | no (this manifest) | This profile does not pin a model. Use the provider key your Hermes install already needs. |

`HONCHO_API_KEY` is `required: false` because self-hosted Honcho does not use it. If you use Honcho Cloud, set the key anyway — the installer will not block you if it is missing.

## Context7 MCP

Official Hermes MCP config lives under `mcp_servers` in `config.yaml`. This distribution also ships `mcp.json` because that filename is in the official distribution-owned list.

Both files use documented interpolation (`${env:CONTEXT7_API_KEY}` / `${CONTEXT7_API_KEY}`), not a literal key.

If your installed Hermes only reads `config.yaml` `mcp_servers` (the documented runtime path), you are already covered. If a future installer merges `mcp.json` instead, the same server is there.

## Honcho

- Shared workspace: `hermes`
- Host block: `hermes.research-bot` (official pattern: `hermes.<profile>`)
- `aiPeer`: `research-bot`
- `recallMode`: `hybrid`
- `writeFrequency`: `async`
- `sessionStrategy`: `per-directory` (documented default). Use `per-repo` only if you want one Honcho session per git root; that is also documented, but this profile often runs from mixed working directories.

Never two writers on this `aiPeer`.

## Toolsets

`custom_toolsets.research` = `web`, `terminal`, `file`, `skills`, `memory`, `session_search`. `toolsets: [research]` selects that bundle. Names from the official toolsets reference.

`terminal.cwd` is `"."` (Gateway/cron). CLI uses the launch directory. Backend is `local` — this profile is not a sandbox.

## Skills

1. `primary-source-research` — Context7, then official docs, then papers.
2. `citation-discipline` — refuse invented citations.
3. `research-brief` — write findings, do not implement.

Shared-later skills go in `../../skills-tap/skills/`, not here.

## Cron

None. Official docs: distribution cron is not auto-scheduled. A weekly digest without a delivery target is not justified for this profile.

## Smoke

```bash
hermes profile install ./agents/research-bot --name research-bot-test --alias
research-bot-test chat
# "Name two primary-source rules from your SOUL. Do not invent a paper."
hermes profile delete research-bot-test --yes
```

Not run in CI (no live Hermes on this repo).
