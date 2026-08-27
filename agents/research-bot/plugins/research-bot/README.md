# research-bot plugin

Execution layer for the **research-bot** profile only. Not a shared army runtime.
Do not enable this plugin on other agents.

Official contract: native Hermes plugin (`plugin.yaml` + `register(ctx)`).
Guide: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
Hooks: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks

## What it provides

Toolset `research-bot`:

| Tool | When skills call it |
|---|---|
| `source_ledger_add` | After `web_search`, `web_extract`, Context7, or reading a paper |
| `source_ledger_list` | To review what has been recorded this session |
| `source_ledger_cite` | Before writing a citation in a brief |
| `source_ledger_check` | Before asserting a factual claim |

Hooks:

- `on_session_start` — create the profile-scoped ledger
- `pre_llm_call` — inject the research contract onto the **user message** (keeps the system-prompt cache)
- `pre_tool_call` — block product-code writes; allow research artifacts
- `post_tool_call` — harvest URLs from retrieval tools into the ledger

Middleware: `tool_request` fills `citation_style` on `source_ledger_cite` when omitted.

## State

Ledger lives in `<HERMES_HOME>/plugin-data/research-bot/` via official
`plugins.plugin_storage.plugin_data_dir`. Never write next to `plugin.yaml`.

Settings (read with `ctx.get_config`):

```yaml
plugins:
  enabled:
    - research-bot
  entries:
    research-bot:
      settings:
        citation_style: apa   # apa | ieee | chicago
        strictness: strict    # strict | relaxed
```

## Skills

Primary skills stay in `agents/research-bot/skills/` (normal skill index) and
declare `metadata.hermes.requires_toolsets: [research-bot]`. They are **not**
`plugin:skill` entries.
