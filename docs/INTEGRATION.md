# Integration notes

**Source of truth:** [`PROFILE-PLAYBOOK.md`](PROFILE-PLAYBOOK.md)

Each profile’s `agents/<name>/INTEGRATION.md` is that profile’s join map: plugin name, toolset, MCP allowlist, skill `requires_tools`, and any official-page locks that profile must obey.

Copy the playbook’s **method**, not another profile’s plugin, tools, or skills.

`research-bot` locks the official join in [`../agents/research-bot/INTEGRATION.md`](../agents/research-bot/INTEGRATION.md), citing:

- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

Native plugin path only. Do not patch Hermes `tools/` or `toolsets.py`. Portable Agent Plugins v1 (`plugin.json`) is not this factory’s path.
