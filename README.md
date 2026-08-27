# hermes-agents

Factory for James Fincher's Hermes Agent **profile distributions**. One directory per agent. Honcho is the shared memory layer. Cursor (and Herbert) add agents one PR at a time.

This is **not** a single GitHub-installable army. Official `hermes profile install github.com/owner/repo` only reads a **repo-root** `distribution.yaml`. Official docs **do** allow `hermes profile install ./path` when the manifest sits at that path. We use the second form.

## Context7 rule

Every Hermes / Honcho / library question starts at Context7, then official LLM entry points. Never invent config knobs from training data.

1. Context7 (Context7-API). Library IDs:
   - `/nousresearch/hermes-agent`
   - `/plastic-labs/honcho`
   - `/llmstxt/hermes-agent_nousresearch_llms_txt`
   - `/websites/honcho_dev_v3`
2. https://hermes-agent.nousresearch.com/llms.txt and https://hermes-agent.nousresearch.com/llms-full.txt
3. Do not clone NousResearch/hermes-agent or James's other repos.

`CONTEXT7_API_KEY` is a GitHub Actions secret. Do not print, log, or commit it.

Cursor agents: read `AGENTS.md` and `docs/WORKFLOW.md`.

## Install the first agent

From a clone of this repo, on a machine with stock Hermes (`~/.hermes`, not Gengar):

```bash
hermes profile install ./agents/research-bot --alias
```

Then fill env keys from the installer's `.env.EXAMPLE`, merge `agents/research-bot/honcho.json.example` into local Honcho config (no secrets in git), and run `hermes memory setup` if Honcho is not already the active provider.

Update:

```bash
hermes profile update research-bot
```

## Army

| Agent | Path | Role |
| --- | --- | --- |
| `research-bot` | `agents/research-bot/` | Reads source + docs + papers, writes cited findings, does not implement product code. Ships `plugins/research-bot/` (enabled only on this profile). |

## Add the next agent

One agent per PR. Checklist is in `AGENTS.md`. Short version:

1. Context7 + official docs for every knob.
2. New directory `agents/<name>/` with `distribution.yaml` at its root.
3. Fill `SOUL.md`, `profile.yaml`, `config.yaml`, `honcho.json.example`, **that agent's plugin** (`plugins/<name>/`), skills that `requires_toolsets: [<name>]`, MCP only if headers can be `${env:VAR}`.
4. Reserved names: `hermes`, `test`, `tmp`, `root`, `sudo`. Do not collide with ouroboros plugin names (`echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`).
5. Smoke locally: `hermes profile install ./agents/<name> --name <name>-test --alias`

Shared skills later: `skills-tap/skills/` (tap path override documented there). New host capability for one agent goes on **that** agent's plugin — no shared army-runtime. See `plugins/README.md`. Do not vendor Gengar or fork Ouroboros.

## License

Apache-2.0. Matches JamesFincher/hermes-ouroboros. Hermes Agent itself is MIT; this repo is profile content, not a fork of the engine.
