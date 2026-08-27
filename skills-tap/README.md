# Shared skill tap

Skills are **recipes** in the normal skill index. Process code lives in `army-runtime`. A distribution carries both. Do not put these recipes in a plugin (`plugin:skill`).

Official tap layout is `skills/<slug>/SKILL.md` at the tap root (default path `skills/`). This factory keeps **shared** recipes here so they are not copied into every agent profile.

```text
skills-tap/skills/<slug>/SKILL.md
```

Agent-local skills stay in `agents/<name>/skills/`.

## Add this repo as a tap

```bash
hermes skills tap add JamesFincher/hermes-agents
```

The CLI default path is `skills/`. This tap is **not** at that default. After adding, set the path in `~/.hermes/skills/.hub/taps.json`:

```json
{
  "taps": [
    {"repo": "JamesFincher/hermes-agents", "path": "skills-tap/skills/"}
  ]
}
```

Private repos need a configured `GITHUB_TOKEN`.

No shared skills ship in the first PR. Add them one per later PR.
