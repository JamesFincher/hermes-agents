# P1 live install (Hermes Agent v0.19.0, pip)

Date: 2026-08-27. CLI: `hermes-agent` 0.19.0 from PyPI. No repo vendored.

```text
hermes profile install /workspace/agents/research-bot --name research-bot-hdr --yes
✓ Installed 'research-bot-hdr' v2.0.0
  Profile path: ~/.hermes/profiles/research-bot-hdr
```

`hermes -p research-bot-hdr tools list` enabled: web, browser, vision, file, terminal, code_execution, skills, memory, session_search, todo, clarify, delegation, cronjob, hdr.

No `moa` toolset line. Official: MoA is a provider.

`hermes -p research-bot-hdr skills list`: claim-audit, deep-research-run, literature-sweep, source-triage, web-fallback-fetch (all local, enabled).

`hermes plugins doctor` is not a command on 0.19.0. See docs/HERMES-FACTS.md.
