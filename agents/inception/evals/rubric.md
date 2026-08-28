# inception rubric

Hand-run once from the shipped files. No live Hermes.

| Task | Gate | Result | Notes |
| --- | --- | --- | --- |
| T01 | scaffold_ok | pass | Plan completes first, then `shelf-note` validates |
| T02 | scaffold_reserved | pass | `hermes` returns `{"error":…}` |
| T03 | probe_doc | pass | `[DOC]` row stored |
| T04 | probe_unv_no_code | pass | `code_depends` on `[UNV]` errors |
| T05 | docs_no_url | pass | Fake MCP with no URL stores no card |
| T06 | check_ok | pass | `check_profile` on the T01 tree |
| T07 | scaffold_ouroboros | pass | `forge` blocked |
| T08 | digest_cap | pass | Digest ≤800 |
| T09 | no_hdr_enable | pass | inception `config.yaml` enables `[inception]` only |
| T10 | scaffold_forbidden | pass | `research-bot` name rejected |
| T11 | scaffold_without_plan | pass | Job line alone cannot scaffold |
| T12 | spec_missing_surfaces | pass | Stub spec without plugin/tool/skill/MCP is refused |
| T13 | counsel_shaped_plan_ok | pass | Fixture plan returns `check_plan` ok |

Score: 13 / 13 gates green in `tests/test_inception_plugin.py`.
