# army-runtime

Shared process layer for every agent in this factory. Toolset: **`army`**.

Skills are recipes in the normal index (`agents/<name>/skills/`, `skills-tap/skills/`).
This plugin is not a skill library. Do not `ctx.register_skill` the primary skills.

Official contract: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

## Enable

Every agent `config.yaml`:

```yaml
memory:
  provider: honcho          # memory plugin — not plugins.enabled
plugins:
  enabled:
    - army-runtime
  entries:
    army-runtime:
      settings:
        citation_style: apa   # apa | ieee | chicago
        write_policy: off     # research | off  (research-bot sets research)
```

`plugins.disabled` always wins. Honcho is never an `enabled` entry.

Each profile is its own `$HERMES_HOME`. Install copies this directory from
`agents/<name>/plugins/army-runtime/` (a copy of this factory source) into
that profile home. Factory source of truth: `plugins/army-runtime/`.
Keep consumer copies identical. Claim `plugins` in `distribution_owned`.

## Tools (toolset `army`)

Built-in web/terminal/file cannot guarantee a structured, de-duplicated,
profile-scoped citation ledger. These tools do.

| Tool | When skills call it |
| --- | --- |
| `source_ledger_add` | After retrieving a page |
| `source_ledger_list` | Before writing findings |
| `source_ledger_cite` | Before citing — use only this formatted text |
| `source_ledger_check` | Before asserting a factual claim |

Handlers: `args` dict, JSON string, `**kwargs`, never raise.

## Hooks

- `on_session_start` — init ledger in `plugin-data/army-runtime/`
- `pre_llm_call` — short army contract on the **user message** (does not dump skill bodies)
- `pre_tool_call` — write policy only when `write_policy: research`
- `post_tool_call` — harvest URLs from retrieval tools

## New host capability

Add the tool here. Declare `requires_tools` / `requires_toolsets: [army]` on the
skill. Same `plugins.enabled: [army-runtime]`. Per-agent plugin only when the
capability must not leak to other profiles.

State: `<HERMES_HOME>/plugin-data/army-runtime/` via `plugin_data_dir`.
