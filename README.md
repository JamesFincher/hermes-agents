# Hermes Agent Profile Library

This repo is the **Hermes Agent Profile Library**. It is a library of independent specialized Hermes profiles. Grow it by adding a new `agents/<name>/` distribution. Pull from it with `hermes profile install ./agents/<name>`. Each profile is complete and isolated. The library is the shelf, not a shared process layer.

Honcho is each profile’s memory provider (`memory.provider: honcho`). Cursor (and Herbert) add agents one PR at a time.

Official `hermes profile install github.com/owner/repo` only reads a **repo-root** `distribution.yaml`. Official docs **do** allow `hermes profile install ./path` when the manifest sits at that path. We use the second form. There is no repo-root `distribution.yaml`.

**How to generate the next profile:** [`docs/PROFILE-PLAYBOOK.md`](docs/PROFILE-PLAYBOOK.md)

**Honest limits** of the shipped research-bot profile: [`docs/HONEST-LIMITS.md`](docs/HONEST-LIMITS.md)

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

## Install a profile

From a clone of this repo, on a machine with stock Hermes (`~/.hermes`, not Gengar):

```bash
hermes profile install ./agents/research-bot --alias
hermes profile install ./agents/inception --alias
```

Then fill env keys from the installer's `.env.EXAMPLE`, merge `agents/research-bot/honcho.json.example` into local Honcho config (no secrets in git), and run `hermes memory setup` if Honcho is not already the active provider.

Update:

```bash
hermes profile update research-bot
```

## Profiles

| Profile | Path | Job | Scarce resource | Headline custom surface |
| --- | --- | --- | --- | --- |
| `research-bot` | `agents/research-bot/` | Reads source + docs + papers, writes cited findings, does not implement product code. Ships **its own** `hdr` plugin and toolset at `plugins/hdr/`. | Evidence tokens | Evidence Bus + Citation Gate + governor |
| `inception` | `agents/inception/` | Authors new isolated Hermes profiles from the playbook. Does not share a runtime. Ships **its own** `inception` plugin and toolset at `plugins/inception/`. | Context tokens | Isolation fence + docs distill + probe ledger |

## Add the next profile

One agent per PR. The playbook is the checklist. Short version:

1. Context7 + official docs for every knob.
2. New directory `agents/<name>/` with `distribution.yaml` at its root. Empty of `research-bot`’s plugin, tools, and skills. No repo-root `plugins/`. Zero imports from `hdr`.
3. Follow [`docs/PROFILE-PLAYBOOK.md`](docs/PROFILE-PLAYBOOK.md): `SOUL.md`, `config.yaml` (`memory.provider: honcho`), **this** profile’s plugin only if it needs tools (`plugins.enabled: [<plugin-id>]`; the id may differ from the profile name), skill recipes in **this** profile’s `skills/` (`metadata.hermes.requires_toolsets` of **this** profile’s toolset), MCP only if **this** plugin will `call_mcp` and headers can be `${env:VAR}`.
4. If the profile uses the web, keep the locked gather block: `web.search_backend: searxng`, `web.extract_backend: firecrawl`, `keyless_fallback` and `keyless_rescue` **true** (degrade, do not die). Do not add a search tool.
5. Reserved names: `hermes`, `test`, `tmp`, `root`, `sudo`. Do not collide with ouroboros plugin names (`echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`).
6. Smoke locally: `hermes profile install ./agents/<name> --name <name>-test --alias`

Do not vendor Gengar or fork Ouroboros.

## License

Apache-2.0. Matches JamesFincher/hermes-ouroboros. Hermes Agent itself is MIT; this repo is profile content, not a fork of the engine.
