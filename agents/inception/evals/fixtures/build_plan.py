"""Counsel-shaped canvas and spec bodies for frozen plan-gate tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CANVAS_TEMPLATE = """# Profile canvas: {name}

## 1. Job
{job} This sentence states the refuse-list so the profile cannot drift into advice or filings.

## 2. Who it beats
{incumbent} on **{axis}**. Eloquence is not the bar. Refusal of unretrieved citations is the bar.

## 3. Mechanisms to reproduce
Retrieval-grounded assertion maps to transform_tool_result. Citation verification maps to a ledger plus a pre_tool_call fence. Required-elements contracts map to plugin data. Placeholder discipline maps to a fact fence. Jurisdiction as the primary axis maps to matter state. Currency dating maps to a status field. Parallel issue research maps to optional delegation that this plan may reject. A separate verification pass maps to a skill plus a check tool. Deterministic date math maps to store rules. Five to ten rows live in the spec.

## 4. The loop
intake to hat to facts to issue plan to authority retrieval to read to scaffold to draft to gates to write. Network is touched only in retrieval. Drafting reads the ledger only. Filesystem holds corpus and audit. The model never invents a cite.

## 5. Scarce resource
Trust. One fabricated citation destroys the profile. Tokens are second. This is why write gates fail closed and why the plan must exist before any agents tree is written.

## 6. Durable state
plugin-data under this profile's plugin id. ledger.json with a version field. corpus write-once. matters and audit jsonl. Survives compaction, /new, and profile update. Not memory.provider.

## 7. Custom surface
Patterns: intercept-and-distil on retrieved opinions, fence on write and citation, free output for the disclaimer footer, ledger for authorities. Four of five §4 patterns. Governor is optional. Tools answer the three questions in the spec. Hooks are policy or transform. Scripts parse citations.

## 8. Fan-out
Rejected or flat depth one. Children return ids and counts, never raw opinions. If fan-out is rejected, say so in the spec and keep orchestrator_enabled false.

## 9. Knob sweep
Every playbook §5 context-economics knob is recorded on this plan via probe_knob. compression.threshold, threshold_tokens, tail_mode, protect_last_n, protect_first_n, in_place, idle_compact_after_seconds, proactive_prune_tokens and companions, tool_output bounds, tool_budget.mcp_result_size_chars, file_read_max_chars, context_file_max_chars, context.engine.

## 10. Failure ladder
Primary corpus down: degrade to a documented public HTTP path and mark unverified. Token missing: every citation unverified, never trusted. MCP absent: explicit none. JS-only portal: browser toolset if the canvas accepted it. Dead link: report the gap. Never substitute a similar authority.

## 11. Eval
Eight or more frozen tasks. Two adversarial: fabrication bait and "fill standard values". Deterministic gates in CI. Rubric floor fails the run on citation integrity.

## 12. Honest limits
The gate proves a citation exists, not that it stands for the proposition. No appearance, no filing, no outcome prediction. Live CLI install may be unproven. Write that in HONEST-LIMITS.md before code.
"""

SPEC_TEMPLATE = """# Profile spec: {name}

Every platform claim is tagged. Code does not depend on [UNV].

## Verdict
Ship a specialist that retrieves primary US law and drafts under a practice hat. It refuses any citation or concrete fact it did not retrieve. It does not advise, file, appear, sign, or predict outcomes. The incumbent is general chat used as a lawyer. The axis is {axis}. Scaffold is not this product. The plan must close first. [INF]

## Incumbent mechanism map
Distilled from published legal-tech write-ups and court-data docs, not from another profile's plugin.

| Mechanism | Why it matters | Hermes surface |
| --- | --- | --- |
| Retrieval-grounded assertion | Stops invented quotes | transform_tool_result plus ledger |
| Citation verification | Public failure mode is fake cites | store plus pre_tool_call fence |
| Required-elements contracts | Forms have mandatory parts | plugin data plus a draft tool |
| Placeholder discipline | Humans leave blanks | fact fence |
| Jurisdiction axis | Law is not national by default | matter record |
| Currency dating | Statutes change | status field |
| Parallel issue research | Coverage without one-window pileup | delegation or explicit reject |
| Separate verification pass | Inline cites degrade both tasks | skill plus check tool |
| Deterministic date math | Deadlines are not inferred | store rules |

## Load-bearing inventions
1. Authority ledger with a version field.
2. Policy write fence that fails closed and says why. [DOC] https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
3. Facades over HTTP. The model never calls raw mcp names.
4. Honest limits written before the first draft tool ships.

## Nine surfaces
SOUL is identity only. config.yaml is the machine with annotated compression and toolsets. MCP is none or a named server with a facade. Plugin is plugins/<id>/ owned by this profile. Tools are schemas plus handlers. Skills are disjoint recipes. Delegation is rejected or flat. Memory is memory.provider honcho with a unique aiPeer. Distribution plus eval ships or the profile does not. [DOC] https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Annotated config
custom_toolsets names this profile's toolset only. plugins.enabled lists that plugin id only. No hdr. No moa toolset. hermes_requires >=0.13.0. [DOC] https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference

## Plugin file map
plugin.yaml, __init__.py register(ctx), runtime.py, schemas.py, store/ledger.py, tools/, hooks/fence.py, hooks/distill.py. No import from hdr. No copy of lex. Path is agents/{name}/plugins/<id>/.

## Full tool schemas
Each tool is a flat object with name, description starting When to call, and parameters. Handlers take args and kwargs, return json.dumps, never raise. Errors are the error key. Cite, fetch, check, and matter tools are listed with required fields in the implementation pass. [DOC] https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools

## Hook table
| Hook | Category | Fail | Role |
| --- | --- | --- | --- |
| pre_tool_call | Policy | closed + why | Citation and path fence |
| transform_tool_result | Transform | open | Intercept-and-distil |
| transform_llm_output | Transform | open | Free output disclaimer |
| pre_api_request | Observer | open | Optional governor count |

## Data schemas
ledger.json version field, authorities[], matters[], audit[]. Corpus files are write-once text keyed by hash. Migration is tested. plugin-data is runtime and is not in the install tree.

## Skill list
Primary draft skill, cite-check skill, and intake skill. Triggers are disjoint. metadata.hermes.requires_toolsets names this profile's toolset. Scripts live under each skill. No CONTEXT7_API_KEY on a skill. [DOC] https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills

## MCP list
Explicit none for a first-party law server. If a later pass adds a public HTTP facade, the plugin registers that tool and calls ctx.call_mcp only for Context7 docs. The model never calls raw mcp names. [INF]

## Delegation topology
Rejected in this fixture. orchestrator_enabled false. Children are out of scope. If a later canvas accepts fan-out, children return ids not opinions.

## Token economics
Frontier parent, cheap unused child. Distil retrieved opinions. Digest cap is plugin-owned. Live cost is [UNV] until measured. Code does not read an unverified billing knob.

## Failure ladder
Corpus down: HTTP fallback, mark unverified. Slow: timeout envelope. Rate-limited: same as down. Lying page: require an openable https URL before a card is trusted. Missing token: refuse to treat cites as verified.

## Eval design
Eight frozen tasks minimum. Two adversarial tasks: fabrication bait and fill-in-the-blanks with standard values. Deterministic CI gates. Rubric floor is zero on citation integrity.

## Phased P1–P10 acceptance
P1 tree and config. P2 store version. P3 hooks. P4 tools. P5 skills. P6 eval. P7 canvas match. P8 honest limits. P9 deep-dive from shipped files. P10 isolation review with check_profile ok.

## Honest limits
Proves existence, not holding. No advice. No filing. No outcome prediction. Isolation fence is not an OS jail. Live hermes CLI may be unproven. Do not invent hermes plugins doctor. Do not ship a repo-root distribution.yaml; that index line is [UNV] and must not ship.
"""


def canvas_markdown(name: str, job: str, incumbent: str, axis: str) -> str:
    return CANVAS_TEMPLATE.format(name=name, job=job, incumbent=incumbent, axis=axis)


def spec_markdown(name: str, axis: str) -> str:
    return SPEC_TEMPLATE.format(name=name, axis=axis)


def load_meta() -> dict[str, Any]:
    path = Path(__file__).with_name("counsel_shaped_plan.json")
    return json.loads(path.read_text(encoding="utf-8"))
