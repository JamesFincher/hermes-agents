# Plugins

Skills are recipes (normal skill index). Plugins are process code. This factory's join layer is **`army-runtime`**.

Official:

- Distributions: https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions
- Load / enable: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- Authoring: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

## army-runtime (shared)

Factory source: `plugins/army-runtime/`

Every agent:

1. Copies that directory to `agents/<name>/plugins/army-runtime/` (keep identical — each profile is its own `$HERMES_HOME`).
2. Sets `plugins.enabled: [army-runtime]`.
3. Claims `plugins` in `distribution_owned` (not in the official default owned set).
4. Adds toolset `army` to a `custom_toolsets` bundle.

Honcho stays `memory.provider: honcho`. Never in `plugins.enabled`. `plugins.disabled` always wins.

Do not `ctx.register_skill` the primary skill library.

**New host capability:** add the tool here, declare `requires_tools` on the skill, same enable list. Recopy into every consumer.

**Per-agent plugin:** only when the capability must not leak. Then `agents/<name>/plugins/<name>/` plus that name on **that** profile's `plugins.enabled`.

State: `<HERMES_HOME>/plugin-data/army-runtime/` via `plugin_data_dir`.

Do not collide with ouroboros names: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.

Do not vendor JamesFincher/gengar. Do not rewrite JamesFincher/hermes-ouroboros.

## Shipped

| Plugin | Kind | Factory path | Enable on |
| --- | --- | --- | --- |
| `army-runtime` | Shared | `plugins/army-runtime/` | every agent |
