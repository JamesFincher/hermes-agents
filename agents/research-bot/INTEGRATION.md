# research-bot instance

**Playbook:** [`../../docs/PROFILE-PLAYBOOK.md`](../../docs/PROFILE-PLAYBOOK.md) §6.

| Layer | This profile |
| --- | --- |
| Plugin | `plugins/research-bot/` |
| `plugins.enabled` | `[research-bot]` |
| Toolset | `research-bot` |
| MCP | `context7` + `mcp_allowlist: [context7]` |
| Skills | `literature-review`, `source-triage`, `claim-check` |
| Skill gate | `requires_toolsets: [research-bot]` + facade / ledger tool names |
| Honcho | settled in playbook (hybrid system recall; `pinUserPeer` gateway-only) |

Do not copy this plugin, these tools, or these skills to the next profile.
