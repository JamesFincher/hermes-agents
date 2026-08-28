# Profile canvas: inception

Checked in before code. Updated to match the shipped files.

## 1. Job

Inception plans a new isolated Hermes profile at counsel and HDR depth, then authors `agents/<name>/` only after `check_plan` is ok. It does not write product apps. It does not share a runtime. Scaffold is not the product.

## 2. Who it beats

The incumbent is a human (or Cursor) walking the playbook by memory. Inception must beat that on **knob honesty** and **isolation**: every config key is probed, and the new profile is empty of `research-bot`, `hdr`, and inception internals.

## 3. Mechanisms to reproduce

| Mechanism | Problem it solves | Hermes surface |
| --- | --- | --- |
| Official docs first | Invented knobs ship as facts | MCP `context7` + facade tools the inception plugin registers |
| Knob ledger | Training-data defaults leak into `config.yaml` | Ledger in `plugin-data/inception/` |
| Plan ledger | Prompted docs-first is dropped at turn 40 | Ledger `plans` in `plugin-data/inception/` |
| Four-track investigation | Tools, skills, MCPs, and plugins go unexamined | Tool `investigate_surface` |
| Canvas and spec writers | Empty sections ship as a plan | Tools `write_canvas` and `write_spec` |
| Plan gate | Scaffold from a job line | Tool `check_plan` + fence |
| Playbook scaffold | Free-form directories fail `validate_factory.py` | Tool `scaffold_profile` after the gate |
| Isolation fence | Reserved names, foreign plugins, secret files, unplanned writes | Hook `pre_tool_call` (policy, fail closed) |
| Payload distill | Context7 blobs ride the window twice | Hook `transform_tool_result` |
| Factory footer | The model drops the step list at turn 40 | Hook `transform_llm_output` |
| Structure check | Review by vibe | Tool `check_profile` |
| Recipe split | Docs pass vs code pass vs review | Skills `plan-profile`, `author-profile`, `probe-knob`, `review-profile` |
| Honcho per home | Memory leaks across profiles | `memory.provider: honcho`, `aiPeer: hermes.inception` |

## 4. The loop

```
plan_start (filesystem: plugin-data)
  → probe official docs (network: Context7 MCP)
  → investigate tool / skill / mcp / plugin
  → write canvas then spec (filesystem)
  → check_plan gate (filesystem, no network)
  → scaffold agents/<name>/ only if ok
  → check_profile
  → review the plan, then the tree
```

Network is Context7 first. Official pages via `web_search` / `web_extract` are the fallback. Scaffold and check do not call the network.

## 5. Scarce resource

Context tokens. Docs payloads and tool schemas are the tax. Distil Context7. Ten registered tools. No fan-out. The plan ledger is the scarce-state save so turn 40 cannot skip investigation.

## 6. Durable state

Survives compaction, `/new`, and profile update. Lives at `<HERMES_HOME>/plugin-data/inception/factory.json`.

```
version: 2
probes[]   id, knob, decision, tag, url, reason, code_depends, plan
cards[]    id, source, openable_url, summary, pointer
scaffolds[] id, name, path, files
checks[]   id, path, gaps
audit[]    id, action, detail
plans{}    one record per target name: job, incumbent, axis, investigations, canvas_path, spec_path, patterns, knob_sweep, check_ok, gaps
```

`plugin-data/` is runtime. It is not in the install tree. Migration is keyed on `version`.

## 7. Custom surface

**Tools** (three questions each):

| Tool | Skill+builtin enough? | Called more than twice? | Undetectable wrong? |
| --- | --- | --- | --- |
| `docs_resolve` | No. Must `ctx.call_mcp`. | Yes. | Yes. Structured envelope. |
| `docs_ask` | No. Same. | Yes. | Yes. Openable URL or no card. |
| `probe_knob` | No. Durable write. | Yes. | Yes. Forces `code_depends=false` on `[UNV]`. |
| `plan_start` | No. Durable open. | Once per name. | Yes. Name gate. |
| `investigate_surface` | No. Must record four tracks. | Yes. | Yes. Structured row. |
| `write_canvas` | No. Must refuse empty §6 sections. | Once per name. | Yes. |
| `write_spec` | No. Must refuse a stub. | Once per name. | Yes. |
| `check_plan` | A script could, but the fence must share the same function. | Yes. | Yes. JSON gaps. |
| `scaffold_profile` | No. Exact tree. Hard-fails without `check_plan` ok. | Once per job. | Yes. Validator-shaped files. |
| `check_profile` | Almost a script. Kept as a tool so the model gets JSON gaps. | Yes during review. | Yes. Structured gaps. |

**Hooks:** `transform_tool_result` (intercept-and-distil), `pre_tool_call` (fence), `transform_llm_output` (free output), `pre_api_request` / `post_api_request` (governor). Ledger is the fifth pattern.

**Scripts:** reserved-name check, tag classifier, heuristic list. Invoked with `${HERMES_SKILL_DIR}`.

**Prompt section:** static factory contract, `after_memory`. Volatile digest ≤800 characters on `pre_llm_call`.

## 8. Fan-out

Rejected. `delegation` is not in the bundle. `orchestrator_enabled: false`. Children are not part of this job. The scarce resource is context, not parallel workers.

## 9. Knob sweep

See `docs/profiles/inception-spec.md` § Knob sweep. Every §5 line has accept / reject / default plus one reason.

## 10. Failure ladder

| Dependency | Down | Slow | Rate-limited | Lying |
| --- | --- | --- | --- | --- |
| Context7 MCP | Facade returns `{"error":…}`. Run continues. Official pages via locked gather. | Timeout → error envelope. | Same as down. | Openable URL required before a card is stored. |
| `validate_factory.py` | `check_profile` returns that error. | N/A (local). | N/A. | Gaps are the source of truth, not the model. |
| Honcho | Profile still authors files. Memory is empty. | Ignore. | Ignore. | Do not treat recall as a knob citation. |
| Local web pair | `keyless_fallback` / `keyless_rescue` stay true. | Degrade. | Degrade. | Distil still wraps untrusted text. |

## 11. Eval

Thirteen frozen tasks in `agents/inception/evals/tasks.jsonl`. Adversarial cases include copy `hdr`, reserved names, and scaffold from a job line. Deterministic gates in `tests/test_inception_plugin.py`. Rubric in `evals/rubric.md`.

## 12. Honest limits

See `agents/inception/HONEST-LIMITS.md`. Live `hermes` CLI is UNPROVEN in this VM. Scaffold is a skeleton, not a finished specialist. Probe tags are only as good as the cited URL.
