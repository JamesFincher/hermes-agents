# Plugins

This factory does not ship a plugin in the first distribution.

Hermes plugins are **opt-in**. Only names listed in a profile's `config.yaml` under `plugins.enabled` load. An empty or missing allow-list loads nothing.

## Hook for later

- Stock Hermes plugins live in `~/.hermes/plugins/` (or the profile's `plugins/` after install).
- Do **not** vendor JamesFincher/gengar (engine, `~/.gengar`).
- Do **not** rewrite JamesFincher/hermes-ouroboros (plugin pack, Apache-2.0). If a later PR needs it, depend on that pack and enable it by name — do not fork it into this tree.
- A later PR that actually ships a plugin must add the code here **and** list it in that agent's `plugins.enabled`. Until then, leave `plugins.enabled` unset.
