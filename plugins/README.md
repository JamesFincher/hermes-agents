# Plugins

A profile distribution **carries** plugins the same way it carries SOUL, config, skills, cron, and MCP. Skills are recipes. Plugins are process code (tools, hooks, middleware).

Official:

- Distributions: https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions
- Load / enable: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- Authoring: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

This factory root is **not** an army-runtime. It is the later extract point for a host primitive two agents already share. Live process code ships inside each agent.

## What is already a plugin

| Need | Official selector | `plugins.enabled`? |
| --- | --- | --- |
| Honcho memory | `memory.provider: honcho` (exclusive memory-provider plugin) | **No** |
| Custom tool / hook / middleware | `$HERMES_HOME/plugins/<name>/` + that profile's `plugins.enabled` | **Yes** |

General plugins do nothing until listed in that profile's `plugins.enabled`. `plugins.disabled` always wins.

## Per-agent vs shared (how the next agent enables)

Each profile is its own `$HERMES_HOME`. Install copies `agents/<name>/plugins/` → `~/.hermes/profiles/<name>/plugins/`.

**Per-agent** (research-bot today):

1. Write `agents/<name>/plugins/<name>/` (`plugin.yaml` + `register(ctx)`).
2. Set that profile's `plugins.enabled` to include `<name>`. Do not enable it on other agents.
3. Claim `plugins` in that agent's `distribution_owned` (not in the official default owned set).
4. Pair skills in `agents/<name>/skills/` with `requires_toolsets: [<name>]` when they need the toolset.

**Shared** (only after two agents copy the same primitive):

1. Extract the common directory to factory `plugins/<shared>/`.
2. Copy it into each consumer as `agents/<consumer>/plugins/<shared>/` (the distribution owns what it ships).
3. Each consumer adds `<shared>` to **its own** `plugins.enabled`. Agents that do not need it omit it (and must not list it).
4. Each consumer that ships `plugins/` claims `plugins` in `distribution_owned`.

Do not invent a dummy plugin to have a folder. Do not put Honcho in `plugins.enabled`. Do not collide with ouroboros names: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.

State: `<HERMES_HOME>/plugin-data/<name>/` via `plugin_data_dir`. Never the install tree.

## Shipped in this factory

| Plugin | Kind | Path | Enable on |
| --- | --- | --- | --- |
| `research-bot` | Per-agent | `agents/research-bot/plugins/research-bot/` | `research-bot` only |

Do not vendor JamesFincher/gengar. Do not rewrite JamesFincher/hermes-ouroboros.
