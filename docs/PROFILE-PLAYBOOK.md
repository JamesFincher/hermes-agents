> Official STOP overlays win when they conflict with the body.
> Hermes 0.19.0 has no `hermes plugins doctor`. Use `plugins list`, `validate_factory.py`, and unit tests.
> No official multi-profile GitHub index. No repo-root `distribution.yaml`. Path install only. The §11 index line is [UNV] / not shipped.
> No `moa` toolset. MoA is a provider (`/moa`, `moa.presets`).
> OpenAlex, PubMed, and Wayback are not first-party Hermes MCP servers. Never reintroduce army / army-runtime / toolset `research-bot`.
> Reserved names: `hermes`, `test`, `tmp`, `root`, `sudo`. Ouroboros collisions: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.

# Hermes Agent Profile Library — Playbook

**What this is.** The rules, the design method, and the reproducible workflow for adding a profile to this library. `research-bot` v2 was produced by running this workflow; §9 contains the prompts to run it again for the next profile.

**What a profile is.** One complete agent: its own `HERMES_HOME`, its own SOUL, its own config, its own plugin, its own skills, its own MCP servers, its own eval. Profiles do not share code. The library is a shelf of finished agents, not a framework with a base class.

---

## 1. The nine surfaces

Every profile is specified across exactly these nine. A profile that leaves a surface at "default" has made a decision and must say so in writing.

| # | Surface | It is | It is not | Cost model |
| --- | --- | --- | --- | --- |
| 1 | **SOUL** | primary identity, slot 1 of the system prompt | not a procedure, not a tool list, not paths | paid once per session, cached |
| 2 | **config.yaml** | the machine: models, budgets, compression, toolsets, sandbox | not personality | free, but every knob has a runtime cost |
| 3 | **MCP** | connected servers | not Hermes tools, not skills, not plugins | payload cost; spills to disk past the MCP threshold |
| 4 | **Plugin** | host package (`plugin.yaml` + `register(ctx)`) that registers tools, hooks, and prompt sections | not a tool | code cost only |
| 5 | **Tools** | schema + handler the model invokes | not a plugin, not a skill | schema in context every turn — the most expensive surface per unit |
| 6 | **Skills** | indexed `SKILL.md` recipes, plus `scripts/` | not tools, no Python in the body | index line always; body only on `skill_view` |
| 7 | **Delegation** | the fan-out topology and child contract | not free parallelism | children are usually the majority of a run's tokens |
| 8 | **Memory** | provider + policy for what is remembered | not the profile's data store | injected per turn — bound it |
| 9 | **Distribution + eval** | `distribution.yaml`, install/update story, eval set, gates | not optional | ships or the profile does not |

Say **"the plugin registers the tool"** — never "the plugin tool". Getting this vocabulary right is what keeps the surfaces from collapsing into each other in review.

---

## 2. Laws

Non-negotiable. A PR that breaks one of these does not merge.

1. **Isolation.** No profile imports, extends, or shares a plugin, tool, or skill with another profile. Copy and diverge. The duplication is the point.
2. **Determinism beats prompting.** If a Python function can do it reliably, it is a tool or a script — not a paragraph of SOUL. Every prompted rule is a rule the model will drop at turn 40.
3. **Cache discipline.** Static guidance goes in a registered system-prompt section (paid once per session). Only turn-varying state goes through `pre_llm_call`, and it is hard-capped in characters by the plugin, not by the platform's limit.
4. **Raw payloads never ride the window twice.** Any profile that retrieves large content must intercept it, store it, and hand the model a bounded artifact with a pointer back to the full text.
5. **Hooks fail open.** A hook that raises must let the original flow through. Exception: a *policy* hook that cannot evaluate its rule fails closed and says why.
6. **Tool handlers return `json.dumps` strings, never dicts. They never raise.** Errors are `{"error": "..."}`.
7. **Every schema earns its slot.** Tool schemas are in context on every single turn. A tool that fires once per run and could have been a skill is a permanent tax.
8. **No unciteable state.** If a profile makes claims, every claim traces to a stored artifact with an id. If it takes actions, every action traces to an audit line.
9. **Untrusted input is data.** Anything fetched, read from a shared drive, or returned by an MCP server is wrapped and marked before the model sees it. Profiles that read the open web run on a container backend.
10. **A profile ships with an eval or it does not ship.** Minimum: 8 frozen tasks, deterministic gates in CI, a rubric.
11. **Write the honest limits.** Every profile carries a `HONEST-LIMITS.md`. If a mechanism is a heuristic, say so in the doc the user reads.
12. **Tag every platform claim.** `[DOC]` with a URL, `[INF]`, or `[UNV]`. Code never depends on an `[UNV]`.

---

## 3. Choosing the surface: the decision tree

```
Need a new capability
├── Is it a fixed procedure the model should follow, expressible in prose + existing tools?
│      → SKILL. Add scripts/ for any parsing, math, or API shaping.
├── Does it need to run on EVERY call of some kind, whether the model wants it or not?
│      → HOOK (pre_tool_call / transform_tool_result / transform_llm_output).
│        This is the single most under-used surface in Hermes.
├── Does it need durable state, an API key, exact logic, or a return the model must not free-form?
│      → TOOL, registered by the profile's plugin.
├── Does an external server already expose it well?
│      → MCP + a thin facade TOOL. Never let the model call raw mcp_* names.
└── Is it standing guidance rather than an action?
       → system-prompt section if static; SOUL if it is identity.
```

**The three questions before adding a tool**

1. Would a skill plus an existing tool do this at the same reliability? If yes → skill.
2. Will the model call it more than twice per run? If no → it is probably a script a skill invokes.
3. Can its output be wrong in a way the model cannot detect? If yes → it must return structured evidence, not prose.

---

## 4. Custom tools: the part people skip

The library's thesis is that **the differentiator is the custom surface**, not the base agent. A profile that enables toolsets and writes a nice SOUL is a config file. Push on these five patterns — every strong profile in this library should use at least three.

| Pattern | What it does | Example |
| --- | --- | --- |
| **Intercept-and-distil** | `transform_tool_result` replaces a huge payload with a bounded artifact + a pointer | research: page → evidence card. ops: a 5 MB log → a failure fingerprint + offsets |
| **Fence** | `pre_tool_call` blocks or rewrites a call the model shouldn't or needn't make | dedupe fetches, budget stops, path allowlists, arg normalization via `modify` |
| **Free output** | `transform_llm_output` adds deterministic content with zero inference | bibliographies, run footers, house-style enforcement, unit normalization |
| **Ledger** | a durable, schema'd store in `plugin-data/` that outlives sessions and compaction | evidence ledger, decision log, incident timeline, portfolio state |
| **Governor** | `pre/post_api_request` accounting + fences = a real per-run circuit breaker | the thing the big research agents are publicly missing |

**Scripts are tools too.** A `scripts/` directory in a skill, invoked by absolute path via the skill-directory token, is the cheapest custom capability in Hermes: no schema tax, no context cost, and the model stops rewriting the same parser every run. Prefer stdlib and curl; document any dependency.

**Anti-patterns**

- A "helper" tool that just reformats what another tool returned → make it a hook.
- A tool whose entire body is an LLM call → that is a skill, or a delegated child.
- Ten narrow tools where three parameterized ones would do → schema bloat.
- A tool that returns prose → the model cannot check it; return structure.

---

## 5. The knob sweep

Before writing a line of code, walk this list and record **accept / reject / default** with a one-line reason for each. Unrecorded knobs are how profiles end up with a research agent compressing on a frontier model at 50 % of the window with tool-result pruning switched off.

**Models and cost**
`model.default` · `delegation.model` / `provider` / `base_url` · `auxiliary.<task>.model` for compression, vision, approval, review, title_generation · `auxiliary.<task>.reasoning_effort` · `auxiliary.<task>.fallback_chain` · `auxiliary.<task>.max_concurrency` · `fallback_providers` · `credential_pool_strategies` · `prompt_caching.cache_ttl`

**Context economics** *(mandatory block — no profile ships without an explicit decision on all of these)*
`compression.threshold` · `threshold_tokens` · `tail_mode` · `protect_last_n` · `protect_first_n` · `in_place` · `idle_compact_after_seconds` · `proactive_prune_tokens` (+ its two companions) · `tool_output.max_bytes` / `max_lines` / `max_line_length` · `tool_budget.mcp_result_size_chars` · `file_read_max_chars` · `context_file_max_chars` · `context.engine`

**Loop control**
`agent.max_turns` · `agent.run_budget_seconds` · `agent.api_max_retries` · `agent.verify_on_stop` / `verify_guidance` / `max_verify_nudges` · `agent.coding_instructions` · `goals.max_turns` · `agent.session_stall_timeout`

**Fan-out**
`delegation.max_concurrent_children` · `max_iterations` · `max_spawn_depth` · `orchestrator_enabled` · `child_timeout_seconds` · `worktree_isolation` · `surface_child_process_notifications`

**Execution surface**
`terminal.backend` (local / docker / ssh / modal / daytona / vercel_sandbox / singularity) · `docker_network` · `docker_mount_cwd_to_workspace` · `docker_forward_env` · `container_*` · `home_mode` · `env_passthrough` · `worktree`

**Capability**
`custom_toolsets.<name>` · `toolsets` · `agent.disabled_toolsets` · per-tool disables · `mcp_servers` + `mcp_allowlist` · `plugins.enabled` · `plugins.stream_reasoning_deltas`

**Memory and skills**
`memory.provider` / limits / `write_approval` · `skills.inline_shell` · `skills.write_approval` · `skills.guard_agent_created` · `skills.config.*`

**Archetype starting points**

| | research | coding | ops / monitoring | analysis |
| --- | --- | --- | --- | --- |
| `terminal.backend` | docker | local | docker | docker |
| `proactive_prune_tokens` | 48 k | 64 k | 32 k | 64 k |
| `tail_mode` | lean | lean | lean | lean |
| `delegation.model` | cheap | same as parent | cheap | cheap |
| `verify_on_stop` | false (custom gate) | true | false | false |
| `run_budget_seconds` | set | unset | set | set |
| headline hook | `transform_tool_result` | `pre_verify` | `pre_tool_call` | `transform_terminal_output` |
| `moa` | verification pass | off | off | consensus on judgement calls |

Note on `moa`: this is a provider (`/moa`, `moa.presets`), not a toolset. Never invent a `moa` toolset.

---

## 6. The design canvas

Fill this in before any code. It is the input to the spec, and it is what review argues about.

```markdown
# Profile canvas: <name>

## 1. Job
One sentence. What it does, and what it explicitly does not do.

## 2. Who it beats
The named incumbent product or workflow this must match or exceed, and on which axis.

## 3. Mechanisms to reproduce
From studying the incumbent: 5-10 mechanisms, each mapped to a Hermes surface.

## 4. The loop
The phase diagram. Which phases touch the network / the filesystem / the model.

## 5. Scarce resource
Tokens? Wall clock? API quota? Human attention? Everything below optimizes this.

## 6. Durable state
What must survive compaction, /new, and profile update. Schema sketch. Where it lives.

## 7. Custom surface
Tools (with the three questions answered), hooks (with category), scripts, prompt sections.

## 8. Fan-out
Topology, child contract, harvest path, what children are forbidden to return.

## 9. Knob sweep
The §5 list, decided.

## 10. Failure ladder
For each external dependency: what happens when it is down, slow, rate-limited, or lying.

## 11. Eval
8-12 frozen tasks incl. 2 adversarial. Deterministic gates. Rubric.

## 12. Honest limits
What this profile is bad at. Written before it is built, updated after.
```

---

## 7. Repository layout

```
agents/<profile>/
  SOUL.md  config.yaml  mcp.json  profile.yaml  distribution.yaml
  honcho.json.example  README.md  HONEST-LIMITS.md  .gitignore
  plugins/<short-id>/
    plugin.yaml  __init__.py  runtime.py  schemas.py
    tools/  hooks/  store/  scripts/
  skills/<skill>/SKILL.md + scripts/
  evals/tasks.jsonl  fixtures/  rubric.md
docs/
  PROFILE-PLAYBOOK.md            # this file
  HERMES-FACTS.md                # shared, versioned platform-fact ledger
  profiles/<profile>-deep-dive.md
```

Do not add a repo-root `distribution.yaml` unless official docs show a real multi-profile GitHub-URL install. Today that is [UNV]. Install is path-only: `hermes profile install ./agents/<name>`.

`plugin-data/` is runtime, never committed, never in the install tree, and therefore always needs a migration path keyed on a `version` field.

**Naming:** plugin/toolset id is short and functional (`hdr`, not `research-bot`) because it appears in the model's tool list. Profile name is the product name. Avoid reserved names (`hermes`, `test`, `tmp`, `root`, `sudo`). `forge` is reserved (ouroboros collision).

---

## 8. Definition of done

A profile PR merges when all of these are true.

- [ ] Canvas (§6) checked in and matches what was built.
- [ ] Every platform claim tagged `[DOC]` with a URL, `[INF]`, or `[UNV]`; no code path depends on `[UNV]`.
- [ ] Knob sweep recorded with a reason per line, including the deliberate defaults.
- [ ] `hermes profile install ./agents/<name> --alias` works from clean. Official CLI 0.19.0 has no `hermes plugins doctor`. Use `hermes plugins list`, this repo's `validate_factory.py`, and unit tests. Do not invent doctor.
- [ ] Static guidance is in prompt sections, not `pre_llm_call`; the volatile injection has an explicit character cap set by the plugin.
- [ ] At least three of the five §4 patterns are present.
- [ ] Every hook fails open (or fails closed *and says why*, for policy hooks).
- [ ] Durable store has a schema `version` and a tested migration.
- [ ] Failure ladder implemented for every external dependency, and a fixture test proves one degradation path.
- [ ] Eval: tasks frozen, deterministic gates in CI on recorded fixtures, rubric run once by hand with results in the PR.
- [ ] Token/run and cost/run measured on 3 eval tasks and recorded in the README.
- [ ] `HONEST-LIMITS.md` written and referenced from the README.
- [ ] Secrets: nothing real committed; `.env.EXAMPLE` complete; no key on a skill; deploy-host-only vars documented as such.
- [ ] Deep-dive doc regenerated from the shipped files, not from the plan.

---

## 9. The workflow (reproducible, Cursor-facing)

Eleven steps. Steps 0–4 produce documents; 5–10 produce code. Each step's prompt is written to be pasted as-is with the bracketed parts filled.

### Step 0 — Platform fact-finding

> Read the current Hermes docs for: configuration, toolsets reference, event hooks, delegation, creating skills, plugins, adding tools, agent loop, prompt assembly, context compression. For each, extract every knob, hook, and contract that a `<PROFILE JOB>` profile could use. Output `docs/HERMES-FACTS.md` as a table: knob/hook · exact name · default · doc URL · one line on why this profile would or would not use it. Do not design anything yet. Flag anything where two doc pages disagree.

Rule: this step runs fresh for every profile. The platform moves; a fact ledger older than a release is a liability.

### Step 1 — Incumbent teardown

> Study how `<INCUMBENT A, B, C>` implement `<CAPABILITY>`. From published engineering write-ups and product docs only. Output: a table of 5–10 concrete mechanisms, what problem each solves, and the evidence it works. Then map each mechanism to a Hermes surface from `HERMES-FACTS.md`. Mark any mechanism with no Hermes equivalent — those are the ones we build custom.

### Step 2 — Canvas

> Fill the profile canvas in `docs/PROFILE-PLAYBOOK.md` §6 for `<PROFILE>`, using the outputs of steps 0 and 1. Be decisive: pick one loop, one scarce resource, one durable schema. Where you are unsure, write `[UNV]` and the probe that would resolve it.

### Step 3 — Gap register (only when updating an existing profile)

> Read `<EXISTING PROFILE DOC OR DIRECTORY>`. Produce a gap register: id, gap, severity S1/S2/S3, the exact evidence in the current files, and the fix reference. Include contradictions between the profile's own documents. Do not propose fixes yet.

### Step 4 — Spec

> Write `docs/profiles/<profile>-spec.md` following the shape of `research-bot-v2-spec.md`: verdict, gap register, incumbent mechanism map, the load-bearing inventions, surface-by-surface changes with complete annotated config, plugin file map, full tool schemas, hook table with categories, data schemas, delegation topology and child contract, token economics table, failure ladder, eval design, phased build order with acceptance criteria, sources, honest limits. Every platform claim carries `[DOC]`/`[INF]`/`[UNV]`.

### Step 5 — Scaffold

> Implement build phase P1 only: directory structure, `config.yaml`, `distribution.yaml`, `profile.yaml`, `mcp.json`, `SOUL.md`, empty plugin with a valid `plugin.yaml` and a `register(ctx)` that registers nothing. Acceptance: profile installs, plugin list is valid, `/tools list` matches the spec's toolset bundle exactly. Do not implement tools yet. Do not invent `plugins doctor`.

### Step 6 — Store

> Implement the durable store: schemas, atomic writes under a lock, `version` field, migration from the previous schema, and unit tests including an 8-thread concurrent-write test and an idempotent-migration test. No hooks, no tools.

### Step 7 — Hooks before tools

> Implement the hook layer: `<the profile's intercept, fence, and free-output hooks>`. Every hook fails open on exception. Add a fixture test per hook proving both the happy path and the fail-open path. Tools come next — do not add them yet.

Order matters: hooks are where the leverage is, and building them first stops the model-facing tool surface from bloating to cover what a hook should have done.

### Step 8 — Tools and prompt sections

> Implement the tools from the spec, exact schemas, `json.dumps` returns, never raising. Register the static system-prompt sections and the capped volatile `pre_llm_call` digest. Assert the digest cap in a test.

### Step 9 — Skills and scripts

> Implement the skills with the documented frontmatter shape, disjoint trigger conditions, correct `requires_*` / `fallback_for_*` gating, and a `scripts/` directory for every parsing or API-shaping step. Invoke scripts by the skill-directory token. Test that a skill hides when its required toolset is absent and that the fallback skill appears when the primary tool is missing.

### Step 10 — Eval, measure, document

> Build the eval set and fixtures, wire the deterministic gates into CI, run the rubric by hand once, measure tokens and cost per run on three tasks, then regenerate the deep-dive doc **from the shipped files** and write `HONEST-LIMITS.md`.

### The reproduction prompt

To regenerate this whole output for a different profile, paste:

> Follow `docs/PROFILE-PLAYBOOK.md` steps 0 through 4 for a new profile named `<NAME>` whose job is `<ONE SENTENCE>` and which must match or exceed `<INCUMBENT>` on `<AXIS>`. Produce two files: `docs/profiles/<NAME>-spec.md` and an updated canvas section. Use `research-bot-v2-spec.md` as the structural template — same section order, same tagging discipline, same level of schema detail. Push hard on custom tools and hooks: the profile must use at least three of the five patterns in playbook §4, and the spec must name which. Do not write implementation code in this pass.

---

## 10. Review heuristics

Questions that reliably find the weak spot in a profile PR.

1. **What is in context on turn 40?** Walk it: system prompt, sections, tool schemas, skill index, memory injection, the last N tool results. If the answer is "I don't know," the profile has no context budget.
2. **What does the second call to the same expensive thing cost?** If the answer isn't "nothing, it's cached or fenced," add the fence.
3. **Which rules are prompted that could be enforced?** Every one of those is a future bug report.
4. **What happens when the primary dependency is down?** If the answer is "the run fails," the failure ladder is missing.
5. **What survives `/new`?** If the profile's value is in the transcript, it evaporates.
6. **What do the children return?** If it is prose containing raw source material, the fan-out is a token amplifier rather than a filter.
7. **Where does untrusted text enter, and what is between it and the terminal?**
8. **What would this profile confidently get wrong?** If nobody can name it, nobody has tested it.
9. **Which surface is doing the most work?** If it is SOUL, the profile is a prompt wearing a directory.

---

## 11. Library conventions

- **Version:** semver per profile. Major on a schema or contract break; minor on new tools or hooks; patch on prompt text and thresholds.
- **`hermes_requires`:** the floor that has *every* feature the profile depends on, not the version you happen to run. List the features in a comment. Use an official example range (`>=0.13.0`), not an invented floor.
- **Config preservation:** `hermes profile update` preserves `config.yaml` unless forced. So any change that *requires* a new knob must fail loudly at session start with a clear message rather than silently running degraded.
- **Deprecation:** a removed tool keeps a stub for one minor version that returns `{"error": "renamed to X"}`. Silent removals strand saved sessions.
- **Docs:** a profile's deep-dive is generated last, from the shipped files. A deep-dive written from the plan documents an agent that does not exist.
- **The library index:** keep a one-line-per-profile table in the root README: name, job, scarce resource, headline custom surface. Do not invent a repo-root `distribution.yaml` until official docs show multi-profile GitHub-URL install.
