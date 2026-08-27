# P9 live skill index — UNPROVEN

Status: **UNPROVEN**. No host has recorded this run. Do not invent CLI output.

Acceptance from `docs/HDR-SPEC.md` §11 P9: with `web_extract` disabled, `web-fallback-fetch` appears and the run still completes.

When a host with Hermes 0.19.0 (or later) records it, replace this file with dated output:

1. Profile name and Hermes version.
2. How `web_extract` was disabled (toolset or skill gate).
3. `hermes -p <name> skills list` showing `web-fallback-fetch`.
4. Whether one fetch still completed via `archive_lookup` / `evidence_add`.

Offline unit test `test_web_fallback_completes_without_web_extract` is not this record. It never asks Hermes to hide or show the skill.
