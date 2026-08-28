# inception rubric

Hand-run once from the shipped files. No live Hermes.

| Task | Gate | Result | Notes |
| --- | --- | --- | --- |
| T01 | scaffold_ok | pass | Unit test writes `shelf-note` and validator accepts it |
| T02 | scaffold_reserved | pass | `hermes` returns `{"error":…}` |
| T03 | probe_doc | pass | `[DOC]` row stored |
| T04 | probe_unv_no_code | pass | `code_depends` on `[UNV]` errors |
| T05 | docs_no_url | pass | Fake MCP with no URL stores no card |
| T06 | check_ok | pass | `check_profile` on the T01 tree |
| T07 | scaffold_ouroboros | pass | `forge` blocked |
| T08 | digest_cap | pass | Digest ≤800 |
| T09 | no_hdr_enable | pass | inception `config.yaml` enables `[inception]` only |
| T10 | scaffold_forbidden | pass | `research-bot` name rejected |

Score: 10 / 10 gates green in `tests/test_inception_plugin.py`.
