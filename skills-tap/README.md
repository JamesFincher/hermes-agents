# Optional skill recipes

Skills are **recipes** in the normal Hermes skill index. They contain no Python. Do not put these recipes in a plugin (`plugin:skill`).

This directory is a Cursor/helper index for recipes that a later profile **may** copy into that profile’s own `skills/`. A profile does not inherit recipes by sitting in this repo. `research-bot` skills stay under `agents/research-bot/skills/`.

Official tap layout is `skills/<slug>/SKILL.md` at the tap root (default path `skills/`).

```text
skills-tap/skills/<slug>/SKILL.md
```

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

No tap skills ship in the first PR. Add them one per later PR, then copy into the profile that needs them.
