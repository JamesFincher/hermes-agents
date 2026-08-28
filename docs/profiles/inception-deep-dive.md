# inception deep-dive

Generated from the shipped files, not from the plan.

## What shipped

`agents/inception/` is a path distribution. `distribution.yaml` name is `inception`, version `1.1.0`, `hermes_requires: ">=0.13.0"`. `distribution_owned` claims `plugins` plus the official defaults this profile still wants.

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
| Tools | `schemas.py` + `tools/*.py`. Ten names. |
| Skills | `skills/plan-profile`, `author-profile`, `probe-knob`, `review-profile`. |
| Delegation | Rejected. `orchestrator_enabled: false`. Bundle omits `delegation`. |
| Memory | `honcho.json.example` host `hermes.inception`, `aiPeer: hermes.inception`, `pinUserPeer: true`. |
| Eval | `evals/tasks.jsonl` (13), `evals/rubric.md`, `tests/test_inception_plugin.py`. |

## Tools the inception plugin registers

From `plugin.yaml` `provides_tools` and `register()`:

- `docs_resolve`
- `docs_ask`
- `probe_knob`
- `plan_start`
- `investigate_surface`
- `write_canvas`
- `write_spec`
- `check_plan`
- `scaffold_profile`
- `check_profile`

Handlers return JSON strings. They never raise.

## Plan gate

`store/plan.py` `evaluate_plan` is the only completeness check. `check_plan` and `hooks/fence.py` both call it. `scaffold_profile` and writes under `agents/<name>/` (except inception's own tree) hard-fail until that function returns ok. A one-line job is not enough.

## Patterns present

From `plugins/inception/hooks/`:

- Intercept-and-distil: `distill.py`
- Fence: `fence.py` (reserved names, secrets, plan gate)
- Free output: `footer.py`
- Ledger: `store/ledger.py` `version: 2` plus `store/plan.py`
- Governor: `governor.py`

## Isolation

`plugins.enabled: [inception]`. No `hdr`. No import of `research_bot_plugin`. Scaffold refuses reserved names, ouroboros ids, `research-bot`, and `inception`.

## Limits

See `agents/inception/HONEST-LIMITS.md`.
