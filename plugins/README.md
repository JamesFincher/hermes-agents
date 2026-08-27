# Plugins

This factory does **not** ship a shared army-runtime. Each profile owns its own plugin, paired to that profile's skills.

| Agent | Plugin path | Enabled on |
| --- | --- | --- |
| `research-bot` | `agents/research-bot/plugins/research-bot/` | `research-bot` only |

Install copies `agents/<name>/plugins/` into that profile's `HERMES_HOME` (`~/.hermes/profiles/<name>/plugins/`). Official discovery is `plugins/<id>/plugin.yaml` + `register(ctx)` under the active home. Guide: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

## Rules

- New agent = new plugin at `agents/<name>/plugins/<name>/`. Enable it only on that profile (`plugins.enabled: [<name>]`).
- Claim `plugins` in that agent's `distribution_owned` so updates replace the execution layer.
- Plugin state goes in profile-scoped `plugin-data/`, never the install tree (`plugin_data_dir`).
- Honcho is `memory.provider: honcho`. Never put Honcho in `plugins.enabled`.
- Do not collide with ouroboros names: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.
- If two later agents copy the same host primitive, extract then. Do not build a generic runtime first.
- Do not vendor JamesFincher/gengar. Do not rewrite JamesFincher/hermes-ouroboros.

Hermes plugins are **opt-in**. Only names listed in a profile's `plugins.enabled` load.
