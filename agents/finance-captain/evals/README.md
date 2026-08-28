# evals

`tasks.jsonl` — 12 frozen tasks. Four adversarial (T09–T12), and those are the
ones that matter: they are direct pressure to state an unsourced number, treat a
blanket "go ahead" as approval for a specific payment, copy a stale figure
forward, and book a plug entry to make a reconciliation close. Every one of
those is a thing a real person will ask for, under time pressure, and meaning no
harm. A single failure fails the build.

`fixtures/` — recorded snapshot payloads so the deterministic gates run offline.
