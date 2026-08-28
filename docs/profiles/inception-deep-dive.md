# inception deep-dive

Generated from the shipped files, not from the plan.

## What shipped

`agents/inception/` is a path distribution. `distribution.yaml` name is `inception`, version `1.0.0`, `hermes_requires: ">=0.13.0"`. `distribution_owned` claims `plugins` plus the official defaults this profile still wants.

Install (docs only; live CLI UNPROVEN):

```bash
hermes profile install ./agents/inception --alias
```

## Nine surfaces in the tree

| Surface | File evidence |
| --- | --- |
| SOUL | `agents/inception/SOUL.md` — librarian identity. No tool names. |
| config.yaml | `agents/inception/config.yaml` — bundle `factory`, locked gather, local terminal. |
| MCP | `mcp.json` + `config.yaml` `mcp_servers.context7`. Allowlist `context7`. |
| Plugin | `plugins/inception/plugin.yaml` + `__init__.py` `register(ctx)`. |
| Tools | `schemas.py` + `tools/*.py`. Five names. |
| Skills | `skills/author-profile`, `probe-knob`, `review-profile`. |
| Delegation | Rejected. `orchestrator_enabled: false`. Bundle omits `delegation`. |
| Memory | `honcho.json.example` host `hermes.inception`, `aiPeer: hermes.inception`, `pinUserPeer: true`. |
| Eval | `evals/tasks.jsonl` (10), `evals/rubric.md`, `tests/test_inception_plugin.py`. |

## Tools the inception plugin registers

From `plugin.yaml` `provides_tools` and `register()`:

- `docs_resolve`
- `docs_ask`
- `probe_knob`
- `scaffold_profile`
- `check_profile`

Handlers return JSON strings. They never raise.

## Patterns present

From `plugins/inception/hooks/`:

- Intercept-and-distil: `distill.py`
- Fence: `fence.py`
- Free output: `footer.py`
- Ledger: `store/ledger.py`
- Governor: `governor.py`

## Isolation

`plugins.enabled: [inception]`. No `hdr`. No import of `research_bot_plugin`. Scaffold refuses reserved names, ouroboros ids, `research-bot`, and `inception`.

## Limits

See `agents/inception/HONEST-LIMITS.md`.
