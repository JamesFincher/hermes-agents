# inception

Authors new isolated Hermes profiles from the playbook. Does not share a runtime.

This profile is one shelf item in the **Hermes Agent Profile Library**. Canvas: [`docs/profiles/inception-canvas.md`](../../docs/profiles/inception-canvas.md). Spec: [`docs/profiles/inception-spec.md`](../../docs/profiles/inception-spec.md). Deep-dive: [`docs/profiles/inception-deep-dive.md`](../../docs/profiles/inception-deep-dive.md). Limits: [`HONEST-LIMITS.md`](HONEST-LIMITS.md).

Scarce resource: context tokens. Headline custom surface: isolation fence + docs distill + probe ledger.

The inception plugin registers tools on toolset `inception`. Skills live in `skills/`. The next profile does not inherit them.

Memory provider is honcho (`memory.provider`). It is not a `plugins.enabled` entry. Unique `aiPeer`: `hermes.inception`. `pinUserPeer: true` is official and gateway-only.

## Install (local path)

```bash
hermes profile install ./agents/inception --alias
```

That copies this directory, including `plugins/inception/`, into `~/.hermes/profiles/inception/`. That directory is `HERMES_HOME`.

Override the name if `inception` already exists:

```bash
hermes profile install ./agents/inception --name inception-test --alias
```

Reserved names: `hermes`, `test`, `tmp`, `root`, `sudo`.

Official GitHub-URL install copies the **repo root** as one payload. There is no official multi-profile index. Do not invent one. Path install only.

## After install

1. Copy env keys from `.env.EXAMPLE` into the profile `.env`.
2. Copy `honcho.json.example` to `honcho.json` (or merge the `hermes.inception` host). Never commit `honcho.json`. `pinUserPeer: true` is gateway-only. The CLI ignores it.
3. `hermes memory setup` if needed.
4. Confirm `plugins.enabled: [inception]`. On Hermes 0.19.0, `hermes plugins` has no `doctor` action. Use `hermes -p inception plugins list` and `hermes -p inception tools list`.

`mcp.json` and `config.yaml` `mcp_servers` must stay twins.

## Tools the inception plugin registers

| Tool | When to call |
| --- | --- |
| `docs_resolve` | Before a new knob. Context7 library id. Openable URL or no card. |
| `docs_ask` | After resolve. One official topic. |
| `probe_knob` | Record accept / reject / default plus `[DOC]` / `[INF]` / `[UNV]`. |
| `scaffold_profile` | Write `agents/<name>/` after the canvas exists. |
| `check_profile` | Run factory validator rules. Returns JSON gaps. |

## Skills

1. `author-profile` — playbook steps 0-4 (docs), then 5-10 (code).
2. `probe-knob` — one knob question.
3. `review-profile` — §10 heuristics plus `check_profile`.

## Token / cost (fixture, 3 tasks)

Live Hermes is UNPROVEN. These numbers are handler output sizes from CI fixtures, estimated as `chars/4` tokens. Cost assumes $0 only because no provider is called.

| Task | Output chars | Est. tokens | Cost |
| --- | --- | --- | --- |
| T03 probe documented knob | 220 | 55 | $0 fixture |
| T01 scaffold valid name | 900 | 225 | $0 fixture |
| T06 check valid skeleton | 180 | 45 | $0 fixture |

## env_requires

| Variable | Required | Why |
| --- | --- | --- |
| `CONTEXT7_API_KEY` | no | Context7 MCP header. Library docs only. Never commit. |
| `HONCHO_API_KEY` | no | Cloud memory. Self-hosted uses `honcho.json` `baseUrl`. |
| `SEARXNG_URL` | deploy host | Locked gather search. |
| `FIRECRAWL_API_URL` | deploy host | Locked gather extract. |
| Model provider key | deploy host | This profile does not pin `model.default`. |

`web.keyless_fallback` and `web.keyless_rescue` are **true**.
