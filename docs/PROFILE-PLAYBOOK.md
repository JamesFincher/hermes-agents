# How to generate one independent specialized Hermes profile

This file is the source of truth for every new agent in this repository.

`hermes-agents` is a **folder of independent profile distributions**. Each profile is a totally independent, highly specialized Hermes agent. Isolated `HERMES_HOME`. Its own `SOUL.md`, `config.yaml`, skills, MCP, and — if it needs custom tools — its own plugin that registers **that profile's** tools. Nothing leaks. This repo is only a place to keep separate distributions side by side. The folder name does not make the profiles one runtime.

`research-bot` is one specialized profile. The next profile starts empty of research-bot's plugin, tools, and skills. Copy the **method** in this playbook. Do not copy research-bot's implementation unless that next profile independently needs the same capability.

Do not clone `NousResearch/hermes-agent`. Read official docs (URLs below). Do not invent knobs. Flag **UNVERIFIED** when official pages disagree or omit a detail. Do not code a dependency on an unverified claim.

---

## 1. What a profile is

A profile is a **separate `HERMES_HOME`**, not a prompt overlay on a shared home.

Official: [User Guide — Profiles](https://hermes-agent.org/docs/user-guide/profiles/), [User Guide — Profile Distributions](https://hermes-agent.org/docs/user-guide/features/profile-distributions/), [Developer Guide — Profile Distributions](https://hermes-agent.org/docs/developer-guide/profile-distributions/).

| Fact | Official source |
| --- | --- |
| Isolated `HERMES_HOME` at `~/.hermes/profiles/<name>/` | [profiles](https://hermes-agent.org/docs/user-guide/profiles/) |
| Never two writers on one home | [profiles — Sharing a Profile Across Machines](https://hermes-agent.org/docs/user-guide/profiles/) |
| `hermes -p <name>` sets `HERMES_HOME` for that process | [profiles](https://hermes-agent.org/docs/user-guide/profiles/) |
| Reserved names: `hermes`, `test`, `tmp`, `root`, `sudo` | [Developer Guide — profile-distributions](https://hermes-agent.org/docs/developer-guide/profile-distributions/) |
| `terminal.cwd: "."` is the **launch directory**, not the profile directory | [Configuration](https://hermes-agent.org/docs/user-guide/configuration/) |
| Profiles are **not sandboxes**. Same user, same filesystem. Isolation is config/state, not OS jail | [profiles — Profiles vs Sandboxing](https://hermes-agent.org/docs/user-guide/profiles/) |
| `config.yaml` is preserved on update unless `--force-config` | [profile-distributions](https://hermes-agent.org/docs/developer-guide/profile-distributions/) |

### `distribution_owned` — plugin is not default

Official default (`DEFAULT_DIST_OWNED` in the developer guide): `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `distribution.yaml`.

**`plugins/` is not in that default.** If a profile ships a plugin, `distribution.yaml` must list `plugins` in `distribution_owned`. Setting that list **replaces** the default — include every default you still want plus `plugins`.

If you omit `plugins` from `distribution_owned`, `hermes profile install` will not ship the plugin. The model will only see builtins + MCP-named tools. That is how a specialized profile silently becomes a generic chatbot.

### Install path

Official `hermes profile install` accepts a **local path** (`hermes profile install ./agents/<name>`) or a GitHub URL. Official GitHub-URL install looks for **repo-root** `distribution.yaml`. This repo keeps many independent distributions under `agents/<name>/`, so local-path install is the supported path. Do not put a repo-root `distribution.yaml`.

---

## 2. Four official surfaces — never collapse them

Official: [User Guide — Skills](https://hermes-agent.org/docs/user-guide/features/skills/), [User Guide — Tools](https://hermes-agent.org/docs/user-guide/features/tools/), [User Guide — Plugins](https://hermes-agent.org/docs/user-guide/features/plugins/), [User Guide — MCP](https://hermes-agent.org/docs/user-guide/features/mcp/), [Developer Guide — Tools](https://hermes-agent.org/docs/developer-guide/tools/), [Developer Guide — Plugins](https://hermes-agent.org/docs/developer-guide/plugins/), [Developer Guide — Skills](https://hermes-agent.org/docs/developer-guide/skills/), [Developer Guide — MCP](https://hermes-agent.org/docs/developer-guide/mcp/).

| Surface | What it is | What it is not | Where it lives | How the model sees it |
| --- | --- | --- | --- | --- |
| **SKILL** | Indexed `SKILL.md` recipe. `skill_view` loads the body. Procedure tells the model which **tools** to call. | Not a tool. Not a plugin. Contains no Python. | This profile's `skills/<name>/SKILL.md` | Progressive disclosure. Gated by `requires_toolsets` / `requires_tools` |
| **TOOL** | Registry schema + handler the model invokes | Not a skill. Not a plugin. | Built-in, **or registered by this profile's plugin**, or MCP-named | Schema in the tool list when its toolset is enabled |
| **PLUGIN** | Host package: `plugin.yaml` + `__init__.py` `register(ctx)` | **Not a tool.** May *register* tools, hooks, middleware, config | This profile's `plugins/<id>/` | Opt-in via `plugins.enabled`. `plugins.disabled` always wins |
| **MCP** | Connected server in `mcp.json` / `mcp_servers` | Not a Hermes tool. Not a skill. Not a plugin | This profile's `mcp.json` + config | Default: MCP-named tools. This factory forbids the model from using those names; the plugin calls MCP |

Say: "the `<profile>` plugin **registers** the `resolve_library` tool."
Do not say: "the plugin tool" as if the plugin *is* the tool.

### Creating Skills (official lock — priority)

Official: [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills). Also [Developer Guide — Skills](https://hermes-agent.org/docs/developer-guide/skills/) and [User Guide — Skills](https://hermes-agent.org/docs/user-guide/features/skills/).

**Skill vs tool (same page):** a skill is instructions + shell + existing tools (arXiv, git, Docker, PDF, CLI/API via `terminal` / `web_extract`). A tool is auth/API keys, must-execute-precisely processing, binary, or streaming. Do not write a plugin tool when a `SKILL.md` plus builtins is enough.

**Where skills live:** profile `skills/<name>/SKILL.md` (indexed). Not `ctx.register_skill` (hidden `plugin:skill`). Not Hermes core `optional-skills/`.

Official [Plugins](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins): `ctx.register_skill` is read-only and **hidden from `<available_skills>`**. The model cannot discover it through the normal index. Use it only for supporting docs a tool already knows about.

**Required `SKILL.md` sections:** When to Use, Quick Reference, Procedure, Pitfalls, Verification. Progressive disclosure. Description frontmatter is the skills-index text — make when-to-use unmistakable. Procedure must name the **tools** the model should call. A skill that never names a tool is a prompt, not a join.

**Hide rules** (all conditions must be met):

| Field | Official hide |
| --- | --- |
| `requires_toolsets` / `requires_tools` | Hidden if **ANY** listed capability is missing |
| `fallback_for_toolsets` / `fallback_for_tools` | Hidden if **ANY** listed capability is present |
| `platforms` | Hidden on incompatible OS. linux is fine. Omit to load on all |
| `required_environment_variables` | Missing does **not** hide the skill. Prompted on `skill_view` in local CLI. Secret never shown to the model. Auto-passthrough into `terminal` / `execute_code` |

Do **not** put `CONTEXT7_API_KEY` on a skill. `ctx.call_mcp` owns that. `required_credential_files` are OAuth files relative to `~/.hermes/` only.

`metadata.hermes.config` stores non-secrets under `skills.config` and injects them on load. Do not duplicate plugin `config_schema` settings (citation style) there.

`${HERMES_SKILL_DIR}` and `${HERMES_SESSION_ID}` are substituted on load. Activation includes `[Skill directory: abs path]`. `inline_shell` (`!`cmd``) is **off** by default — do not enable. `[[as_document]]` for high-res media. Helper `scripts/` only when parsing cannot live in the plugin.

**Blueprints:** installing a blueprint only **suggests** a cron job; never auto-schedules. Do not add `metadata.hermes.blueprint` unless a scheduled job was requested.

Local test (not CI): `hermes chat --toolsets skills -q "Use the X skill to do Y"`

For a specialized profile, gate every workflow skill on **that profile's** toolset plus the exact registered tool names the Procedure calls.

---

## 3. How to generate one specialized profile

Do this in order. Do not skip to copying another profile's plugin.

### Step 0 — Name and isolation

1. Pick a directory `agents/<name>/`. `<name>` must not be reserved (`hermes`, `test`, `tmp`, `root`, `sudo`).
2. That directory **is** the distribution root (`distribution.yaml` lives here).
3. After install, Hermes will use `~/.hermes/profiles/<name>/` as `HERMES_HOME`.
4. This profile does not inherit another profile's plugin, tools, skills, MCP, or SOUL.

### Step 1 — Identity (`SOUL.md`)

Official: [User Guide — Personality](https://hermes-agent.org/docs/user-guide/features/personality/), [User Guide — Use SOUL.md](https://hermes-agent.org/docs/user-guide/guides/use-soul-with-hermes/), [Developer Guide — Prompt Assembly](https://hermes-agent.org/docs/developer-guide/prompt-assembly/).

- Hermes loads **`$HERMES_HOME/SOUL.md` only**. Not project-cwd `SOUL.md`.
- SOUL is identity and tone. Not project paths. Not "query Context7 MCP directly."
- Subagents skip SOUL (`skip_context_files`, `DEFAULT_AGENT_IDENTITY`). Workflow that must survive delegation belongs in the **plugin + skills**, not SOUL alone.
- This repo's root `AGENTS.md` is Cursor workflow. Hermes loads cwd `AGENTS.md` only when no `.hermes.md` / `HERMES.md` exists. Do not rely on repo `AGENTS.md` as the Hermes contract.

### Step 2 — Decide the footprint (official ladder)

Official: [Adding Tools](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools), [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills), [Built-in Plugins](https://hermes-agent.org/docs/user-guide/features/built-in-plugins/).

1. **Skill only** — instructions + existing Hermes tools (`web_search`, `write_file`, …). No plugin. Official [Adding Tools](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools): skill when the job is instructions + shell + existing tools (arXiv, git, Docker, PDF).
2. **Register a tool** on **this profile's native plugin** when you need a schema the model can call (API keys, custom processing, binary, streaming).
3. **Ship a general plugin** when you need hooks, `plugin-data`, or `ctx.call_mcp`. Native path only: `plugin.yaml` + `__init__.py` `register(ctx)`. Not Portable Agent Plugins v1 (`plugin.json`).
4. **Add an MCP server** so the **plugin** can `call_mcp`. Not so the model roams `mcp_*`.
5. **Never** a new Hermes core tool. The adding-tools page is **built-in core only** (`tools/` + `toolsets.py`). Custom tools **must** use the plugin route. Do not patch Hermes core.

If the job is "follow a recipe with builtins," stop at a skill. `research-bot` needed a plugin because Context7 must be called through `ctx.call_mcp` and the ledger must be durable. The next profile may need nothing of that.

### When not to write a plugin

Official sibling plugin types exist for: memory provider, context engine, model provider, secret source, image/video/web-search/browser/terminal backends, platform adapters ([Developer Guide — Plugins](https://hermes-agent.org/docs/developer-guide/plugins/)).

A specialized profile in this repo ships a **general** plugin only (`register(ctx)` + tools/hooks). Do not write a second memory provider. Honcho is already the memory provider (`memory.provider: honcho`). Do not put Honcho in `plugins.enabled`.

### Step 3 — This profile's plugin (only if Step 2 requires it)

Official: [Developer Guide — Plugins](https://hermes-agent.org/docs/developer-guide/plugins/).

```
agents/<name>/plugins/<name>/
  plugin.yaml          # name: <name>  — must match plugins.enabled
  __init__.py          # def register(ctx): ...
```

Discovery (expected, **UNVERIFIED exact glob**): `$HERMES_HOME/plugins/<name>/plugin.yaml`.

`register(ctx)` may:

- `ctx.register_tool(name, handler, schema=..., toolset=<name>, …)` — each tool is a **tool**, registered by the plugin
- `ctx.register_hook(...)` — `on_session_start`, `pre_llm_call`, `pre_tool_call`, `post_tool_call`
- `ctx.get_config` / `ctx.get_plugin_config` / `ctx.plugin_data_dir` (`<HERMES_HOME>/plugin-data/<plugin-name>/`)

`plugin.yaml` `toolsets:` declares toolset ids this plugin **provides**. `config.yaml` `toolsets:` / `custom_toolsets` must **enable** those ids or the registered tools stay hidden.

`plugins.enabled: [<name>]`. `plugins.disabled` always wins. Default-off: `plugins.entries.<id>.mcp_allowlist` — list the MCP **server names** this plugin may call. No wildcards.

Do not collide with ouroboros plugin names: `echo`, `archive`, `seatbelt`, `council`, `autopilot`, `forge`.

The next profile does **not** copy this plugin. If it needs tools, it writes `agents/<next>/plugins/<next>/` from scratch.

### Step 4 — This profile's toolset

Official: [User Guide — Tools](https://hermes-agent.org/docs/user-guide/features/tools/), [Toolsets Reference](https://hermes-agent.org/docs/reference/toolsets-reference/).

- Built-in toolset ids include `web`, `search`, `terminal`, `file`, `browser`, `image`, `tts`, `cron`, `code_execution`, `memory`, `todo`, `session_search`, `skills`, `delegation`.
- `platform_toolsets.cli` was **not found** in official docs. Official knobs are `toolsets` and `custom_toolsets`. The CLI default bundle name is `hermes-cli`.
- This profile invents **one** toolset id, typically the profile name (`research-bot`). Plugin-registered tools use `toolset="<name>"`.
- `custom_toolsets.<bundle>` is a **bundle of toolset ids**, not a list of tool names. Include `skills` plus the builtins the workflow needs plus **this profile's** toolset.
- `toolsets: [<bundle>]` enables that bundle.

The next profile invents its own toolset id. It does not enable `research-bot`.

### Step 5 — MCP (only if the plugin must call a server)

Official: [User Guide — MCP](https://hermes-agent.org/docs/user-guide/features/mcp/), [Use MCP with Hermes](https://hermes-agent.org/docs/user-guide/guides/use-mcp-with-hermes/), [Developer Guide — MCP](https://hermes-agent.org/docs/developer-guide/mcp/), [MCP Config Reference](https://hermes-agent.org/docs/reference/mcp-config-reference/).

Keep Context7 (or whatever server) as `url` + `${env:CONTEXT7_API_KEY}` (or that server's env var).

Do **not** set `tools.include: []`. Official: empty include is treated as unset (all tools).
Do **not** set `enabled: false`. Official: skipped entirely; `ctx.call_mcp` cannot reach it.

`ctx.call_mcp(server, tool, arguments)` is the guaranteed plugin↔MCP join. Server = `mcp.json` name (`context7`). Tool = **unsanitized** MCP name (`resolve-library-id`, `query-docs`).

**Sanitize conflict — UNVERIFIED, do not code a dependency:**

| Source | Pattern | Implied Context7 name |
| --- | --- | --- |
| User-guide MCP + native-mcp.md | `mcp_{server}_{tool}`, hyphens → underscores | `mcp_context7_resolve_library_id` |
| MCP page example `create-issue` | hyphen kept in the example table | `mcp_github_create_issue` |
| mcp-config-reference | `mcp__<server>__<tool>` | `mcp__context7__resolve-library-id` |

Skills `requires_tools` use **facade** names (`resolve_library`), never `mcp_*`.
`ctx.call_mcp` uses unsanitized names.

Official MCP guide says the model *can* use MCP tools like normal tools. This factory's contract: the model uses facade tools; the plugin calls MCP. Do not claim official Hermes hides MCP tools — **UNVERIFIED**. Do not use `include: []` or `enabled: false` to attempt a hide.

### Step 6 — Skills that require **this** profile's toolset

Each workflow skill:

```yaml
requires_toolsets:
  - <this-profile-toolset>
requires_tools:
  - <exact registered names the Procedure calls>
related_skills:
  - <this profile's other workflow skills>
```

If you write `requires_toolsets: [research-bot]` on a different profile's skill, that skill will be **hidden** on the new profile. That is correct: the new profile does not have research-bot's tools.

Do not put `CONTEXT7_API_KEY` in skill env. Do not add a blueprint unless a scheduled job was requested. `research-bot` skills require `resolve_library`, `docs_query`, and `cite_source` by those exact registered names.

### Step 7 — Honcho (one paragraph, then stop)

Official: [User Guide — Memory](https://hermes-agent.org/docs/user-guide/features/memory/), [Developer Guide — Memory](https://hermes-agent.org/docs/developer-guide/memory/), [Memory Providers](https://hermes-agent.org/docs/developer-guide/memory-providers/), [honcho.dev Hermes Agent](https://docs.honcho.dev/v3/guides/agent-frameworks/hermes-agent).

`memory.provider: honcho`. Never in `plugins.enabled`. Each profile is its own `HERMES_HOME`, so Honcho isolation is per home. Use a unique `aiPeer` per profile. Hermes sends `hermes.<profile>` as the Honcho peer. `recallMode: hybrid` injects into the **system** prompt.

`pinUserPeer: true` is official and **GATEWAY-ONLY**. It collapses non-agent gateway users onto `peerName`. It does **not** change CLI identity. Off-gateway the key does nothing. Safe to ship in `honcho.json.example`.

Prefer the Hermes Honcho tool table (`honcho_profile`, `honcho_search`, `honcho_context`, `honcho_reasoning`, `honcho_conclude`) over honcho.dev's older 4-tool list. Do not write a second memory provider. Do not expand Honcho knobs.

### Step 8 — Package files

| File | Role |
| --- | --- |
| `distribution.yaml` | `name`, `description`, `version`, `hermes_min_version`, `distribution_owned` (include `plugins` if you ship one) |
| `config.yaml` | `model`, `memory.provider: honcho`, `toolsets`, `custom_toolsets`, `mcp_servers`, `plugins.enabled: [<this-plugin>]` if any |
| `mcp.json` | MCP servers this plugin may call |
| `SOUL.md` | Identity only |
| `honcho.json.example` | Template; include `pinUserPeer: true` with a comment that it is gateway-only |
| `INTEGRATION.md` | This profile's join map; must not contradict this playbook |
| `LICENSE` | Apache-2.0 |

---

## 4. One-turn join (the model must be able to finish)

Official pages James locked (read these, not training data):

- [Agent Loop Internals](https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop)
- [Prompt Assembly](https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly)
- [Adding Tools](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools)
- [Plugins](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)
- [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills) (priority)
- [Plugin LLM Access](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access)
- [Subagent Lifecycle API](https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api)
- [Memory Provider Plugin](https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin)

Also: [Tools Runtime](https://hermes-agent.org/docs/developer-guide/tools-runtime/), [Hooks](https://hermes-agent.org/docs/developer-guide/hooks/), [Sessions](https://hermes-agent.org/docs/developer-guide/sessions/).

A profile that ships a plugin must encode the join in `agents/<name>/INTEGRATION.md` and cite those URLs. `research-bot` already does.

### Cached system prompt

Three tiers, joined **stable → context → volatile** (`agent/system_prompt.py`). Built **once** on the first turn and reused from the session DB. Rebuild only if model, provider, cwd, or platform changes, or compression rebuild. **Not** because `MEMORY.md` or project files changed mid-session. Mid-session memory writes update disk only until rebuild.

| Tier | Official contents | Do not put here |
| --- | --- | --- |
| **Stable** | `SOUL.md` identity, tool/model guidance, skills **index**, env hints, `platform_hints` | Turn-varying ledger digest |
| **Context** | Caller `system_message` + **one** project file (`.hermes.md`/`HERMES.md` walk-to-git-root, else cwd `AGENTS.md`, else `CLAUDE.md`, else `.cursorrules`). First match wins. | This repo’s root `AGENTS.md` (Cursor workflow; not loaded unless it is the cwd project file and nothing higher-priority exists) |
| **Volatile** (still cached system) | `MEMORY.md` snapshot, `USER.md` snapshot, first-turn Honcho/external memory-provider block, timestamp/session/model line | Live per-turn ledger text |

Skills are **stable**. Memory/Honcho snapshots are **volatile** but still in the cached system prompt, not mid-turn overlays.

**API-call-time only** (not cached system): `ephemeral_system_prompt`, prefill messages, gateway session overlays, later-turn Honcho/external recall on the **user** message, and `pre_llm_call` plugin context on the **user** message. Multiple plugin contexts concatenate.

`pre_llm_call`: return `{context: str}` / `str` / `None`. User message. 10,000 character cap. Fail-open. Put the research contract + live ledger digest here. Never put turn-varying text in SOUL or `config.yaml` `system_message`.

`skip_context_files` (subagent delegation): SOUL is **not** loaded; `DEFAULT_AGENT_IDENTITY` is used. Workflow must live in the plugin + skills, not SOUL alone. SOUL is `$HERMES_HOME/SOUL.md`, security-scanned, truncated (20k floor). `skip_soul` prevents double injection as a context file.

Customize via SOUL / MEMORY / USER / project context / skills / optional system prompt / ephemeral overlays. Do **not** fork `prompt_builder.py`.

### Tool path

Official agent-loop: agent-level tools `todo`, `memory`, `session_search`, `delegate_task` are intercepted **before** `handle_function_call` / registry. They return synthetic results. **Do not** rely on `pre_tool_call` / `post_tool_call` to police them.

Registry tools: resolve `tools/registry.py` → `pre_tool_call` → `approval.py` if dangerous → handler → `post_tool_call` → append `role=tool`. Multiple `tool_calls` run concurrent `ThreadPoolExecutor`; interactive tools (`clarify`) force sequential; results reinserted in original order. Ledger writes must be thread-safe.

`IterationBudget` default 500 (`agent.max_turns`). Subagents get independent budgets capped at `delegation.max_iterations` (default 50).

`pre_tool_call` return: `{action: "block"|"approve"|"modify", message: ...}` or `None`. Official docs cover builtin + plugin tools. MCP-through-hooks is **UNVERIFIED**. Do not harvest or block raw `mcp_*` until verified. Backup-harvest **facade** tools only.

Interrupt abandons the API thread; no partial response enters history.

### Compression (agent-loop)

Preflight if conversation >50% of the context window. Gateway auto-compression >85% between turns.

Order: flush memory to disk **first**, summarize middle turns, keep `protect_last_n` (default 20), never split tool/result pairs, generate a new session lineage id (child session).

**Overlap flag:** the [context-compression](https://hermes-agent.org/docs/developer-guide/context-compression-and-caching/) page also documents `in_place: true` as a default. Agent-loop (the page James locked) says compression creates a **child** session. Do not code a dependency on `in_place`. A durable store must survive child-session lineage: `<HERMES_HOME>/plugin-data/<plugin>/`, not keyed only to a discarded session id.

After each turn: session SQLite persist; `MEMORY.md` / `USER.md` flush. Honcho is `memory.provider` — do not also write a parallel `MEMORY.md` personality from a profile plugin.

### Plugin LLM (`ctx.llm` — out of band)

Official: [Plugin LLM Access](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access).

`ctx.llm` is **not** a tool. No tool loop, no conversation state. Use `complete` / `complete_structured` (and async twins) for extract/score/rewrite jobs the agent should not sit in. Default model is the user's active provider. `provider=` / `model=` / `agent_id=` / `profile=` raise `PluginLlmTrustError` unless `plugins.entries.<id>.llm` `allow_*` grants — do not request those grants unless needed. `purpose=` is required for frequent calls. Cost is the user's paid provider; do not loop `ctx.llm` on every hook. If `complete_structured` returns `parsed is None`, use `result.text`. This does **not** replace `register_tool`. Agent-facing work stays tools + skills.

### Delegation and `ctx.subagent_lifecycle`

Official: [Delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation), [Delegation Patterns](https://hermes-agent.nousresearch.com/docs/guides/delegation-patterns), [Subagent Lifecycle API](https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api), plus prompt-assembly `skip_context_files`.

Keep three paths distinct:

1. `delegate_task` — model-facing **tool** (toolset `delegation`). Children inherit parent toolsets. No model-facing toolsets param.
2. `ctx.subagent_lifecycle.launch` — **plugin** host API. Same child path as `delegate_task`. Only during an active agent turn. Outside a turn: fail-closed `No active Hermes parent session`.
3. SOUL is skipped on children. The specialized contract must live in plugin + skills (and be pasted into `goal`/`context`).

`allowed_toolsets` **narrows** the child. Unknown or parent-broadening toolsets are rejected. Do not give a research child write or product toolsets. Handles are opaque; persist `handle.to_dict()`; after process restart reconnect is `RECONNECT_UNAVAILABLE`. In-process results ~1 hour. Terminal results 32k, no transcripts/hidden reasoning.

Do not invent a child-pool shared across profiles.

### Security

Official: [Security](https://hermes-agent.org/docs/user-guide/security/). `terminal.cwd: "."` is not a jail. `pre_tool_call` can block a tool call; it is not an OS sandbox.

---

## 5. Decision tree

```
Need the model to follow a recipe with existing Hermes tools?
  → Skill only. Stop.

Need a schema the model can invoke (facade, ledger, domain verb)?
  → This profile's plugin registers that tool. toolset = this profile's id.

Need hooks, plugin-data, or ctx.call_mcp?
  → Same plugin. Still this profile only.

Need an external API Hermes does not speak?
  → MCP server in THIS profile's mcp.json.
    Plugin calls ctx.call_mcp.
    Model sees facade tools, not mcp_*.

Need memory?
  → memory.provider: honcho. Not a plugin. Not a second provider.

Need a new Hermes core tool?
  → No. Stop.
```

---

## 6. research-bot is an example, not a template to clone

`research-bot` is one specialized profile that happened to need:

| Layer | research-bot value | Next profile |
| --- | --- | --- |
| Plugin | `agents/research-bot/plugins/research-bot/` | Empty unless *it* needs tools |
| `plugins.enabled` | `[research-bot]` | `[<its-plugin>]` or omit |
| Toolset | `research-bot` | Its own id |
| MCP | server `context7`; `mcp_allowlist: [context7]` | Only if *it* calls a server |
| Skills | `literature-review`, `source-triage`, `claim-check` | Its own recipes |
| Skill gate | `requires_toolsets: [research-bot]` + `requires_tools: [resolve_library, docs_query, cite_source]` | `requires_toolsets: [<its-toolset>]` + that profile's registered names |
| Bundle | `custom_toolsets.research` includes `research-bot` | Its own bundle |
| Facade tools | `resolve_library`, `docs_query` | Whatever *it* registers |
| Ledger tools | `source_ledger_add`, `source_ledger_list`, `cite_source`, `source_ledger_check` | Only if *it* needs a ledger |

research-bot hooks (this profile only): `on_session_start` inits the ledger; `pre_llm_call` injects the contract + digest on the **user** message; `pre_tool_call` blocks product-code writes and scaffolding terminal (does not police `todo`/`memory`/`session_search`/`delegate_task`); `post_tool_call` backup-harvests facade tools, not `mcp_*`. Ledger path is profile `plugin-data/`, not a session id.

SOUL does not tell the model to query Context7 MCP directly.

---

## 7. Factory repo vs Hermes home

| This git repo | Installed Hermes home |
| --- | --- |
| `agents/<name>/` = one distribution | `~/.hermes/profiles/<name>/` |
| `docs/PROFILE-PLAYBOOK.md` = how to generate the next profile | Not installed into Hermes |
| Root `AGENTS.md` = Cursor workflow | Not the Hermes contract |
| No shared plugin directory | Each home has only that profile's `plugins/` |
| `skills-tap/` = Cursor helper index | Not a Hermes skill path unless a profile copies a skill into its own `skills/` |

CI validates structure. It does not run Hermes.

---

## 8. Official pages this playbook used

[Profiles](https://hermes-agent.org/docs/user-guide/profiles/) · [Profile distributions (user)](https://hermes-agent.org/docs/user-guide/features/profile-distributions/) · [Profile distributions (dev)](https://hermes-agent.org/docs/developer-guide/profile-distributions/) · [Which file does what](https://hermes-agent.org/docs/user-guide/which-file-does-what/) · [Configuration](https://hermes-agent.org/docs/user-guide/configuration/) · [Plugins (user)](https://hermes-agent.org/docs/user-guide/features/plugins/) · [Skills (user)](https://hermes-agent.org/docs/user-guide/features/skills/) · [Tools (user)](https://hermes-agent.org/docs/user-guide/features/tools/) · [MCP (user)](https://hermes-agent.org/docs/user-guide/features/mcp/) · [Hooks (user)](https://hermes-agent.org/docs/user-guide/features/hooks/) · [Memory (user)](https://hermes-agent.org/docs/user-guide/features/memory/) · [Personality](https://hermes-agent.org/docs/user-guide/features/personality/) · [Delegation](https://hermes-agent.org/docs/user-guide/features/delegation/) · [Built-in plugins](https://hermes-agent.org/docs/user-guide/features/built-in-plugins/) · [Tools reference](https://hermes-agent.org/docs/reference/tools-reference/) · [Toolsets reference](https://hermes-agent.org/docs/reference/toolsets-reference/) · [MCP config reference](https://hermes-agent.org/docs/reference/mcp-config-reference/) · [Profile commands](https://hermes-agent.org/docs/reference/cli/profile/) · [Use MCP](https://hermes-agent.org/docs/user-guide/guides/use-mcp-with-hermes/) · [Work with skills](https://hermes-agent.org/docs/user-guide/guides/work-with-skills/) · [Use SOUL](https://hermes-agent.org/docs/user-guide/guides/use-soul-with-hermes/) · [Delegation patterns](https://hermes-agent.org/docs/user-guide/guides/delegation-patterns/) · [Agent loop (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop) · [Prompt assembly (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly) · [Adding tools (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools) · [Plugins native (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) · [Creating skills (locked, priority)](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills) · [Plugin LLM access (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access) · [Subagent lifecycle (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api) · [Memory provider plugin (locked)](https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin) · [Skills (dev)](https://hermes-agent.org/docs/developer-guide/skills/) · [MCP (dev)](https://hermes-agent.org/docs/developer-guide/mcp/) · [Hooks (dev)](https://hermes-agent.org/docs/developer-guide/hooks/) · [Tools (dev)](https://hermes-agent.org/docs/developer-guide/tools/) · [Tools runtime](https://hermes-agent.org/docs/developer-guide/tools-runtime/) · [Context compression](https://hermes-agent.org/docs/developer-guide/context-compression-and-caching/) · [Memory (dev)](https://hermes-agent.org/docs/developer-guide/memory/) · [Memory providers](https://hermes-agent.org/docs/developer-guide/memory-providers/) · [Sessions](https://hermes-agent.org/docs/developer-guide/sessions/) · [Security](https://hermes-agent.org/docs/user-guide/security/) · [Multi-profile gateways](https://hermes-agent.org/docs/user-guide/features/multi-profile-gateways/) · [Honcho × Hermes](https://docs.honcho.dev/v3/guides/agent-frameworks/hermes-agent)

Context7 library: `/nousresearch/hermes-agent`. Honcho: `/plastic-labs/honcho` only for the short memory paragraph.
