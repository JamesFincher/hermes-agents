# Profile canvas: inception

Checked in before code. Updated to match the shipped files.

## 1. Job

Inception authors a new isolated `agents/<name>/` distribution from `docs/PROFILE-PLAYBOOK.md`. It does not write product apps. It does not share a runtime.

## 2. Who it beats

The incumbent is a human (or Cursor) walking the playbook by memory. Inception must beat that on **knob honesty** and **isolation**: every config key is probed, and the new profile is empty of `research-bot`, `hdr`, and inception internals.

## 3. Mechanisms to reproduce

| Mechanism | Problem it solves | Hermes surface |
| --- | --- | --- |
| Official docs first | Invented knobs ship as facts | MCP `context7` + facade tools the inception plugin registers |
| Knob ledger | Training-data defaults leak into `config.yaml` | Ledger in `plugin-data/inception/` |
| Playbook scaffold | Free-form directories fail `validate_factory.py` | Tool `scaffold_profile` |
| Isolation fence | Reserved names, foreign plugins, secret files | Hook `pre_tool_call` (policy, fail closed) |
| Payload distill | Context7 blobs ride the window twice | Hook `transform_tool_result` |
| Factory footer | The model drops the step list at turn 40 | Hook `transform_llm_output` |
| Structure check | Review by vibe | Tool `check_profile` |
| Recipe split | Docs pass vs code pass vs review | Skills `author-profile`, `probe-knob`, `review-profile` |
| Honcho per home | Memory leaks across profiles | `memory.provider: honcho`, `aiPeer: hermes.inception` |

## 4. The loop

```
probe official docs (network: Context7 MCP)
  → record knob (filesystem: plugin-data)
  → write canvas/spec (filesystem + model)
  → scaffold agents/<name>/ (filesystem)
  → check (filesystem, no network)
  → review heuristics (model + check_profile)
```

Network is Context7 first. Official pages via `web_search` / `web_extract` are the fallback. Scaffold and check do not call the network.

## 5. Scarce resource

Context tokens. Docs payloads and tool schemas are the tax. Distil Context7. Five registered tools only. No fan-out.

## 6. Durable state

Survives compaction, `/new`, and profile update. Lives at `<HERMES_HOME>/plugin-data/inception/factory.json`.

```
version: 1
probes[]   id, knob, decision, tag, url, reason, code_depends
cards[]    id, source, openable_url, summary, pointer
scaffolds[] id, name, path, files
checks[]   id, path, gaps
audit[]    id, action, detail
```

`plugin-data/` is runtime. It is not in the install tree. Migration is keyed on `version`.

## 7. Custom surface

**Tools** (three questions each):

| Tool | Skill+builtin enough? | Called more than twice? | Undetectable wrong? |
| --- | --- | --- | --- |
| `docs_resolve` | No. Must `ctx.call_mcp`. | Yes. | Yes. Structured envelope. |
| `docs_ask` | No. Same. | Yes. | Yes. Openable URL or no card. |
| `probe_knob` | No. Durable write. | Yes. | Yes. Forces `code_depends=false` on `[UNV]`. |
| `scaffold_profile` | No. Exact tree. | Once per job, but must not be free-form. | Yes. Validator-shaped files. |
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

Ten frozen tasks in `agents/inception/evals/tasks.jsonl`. Two are adversarial (copy `hdr`; reserved name). Deterministic gates in `tests/test_inception_plugin.py`. Rubric in `evals/rubric.md`.

## 12. Honest limits

See `agents/inception/HONEST-LIMITS.md`. Live `hermes` CLI is UNPROVEN in this VM. Scaffold is a skeleton, not a finished specialist. Probe tags are only as good as the cited URL.
