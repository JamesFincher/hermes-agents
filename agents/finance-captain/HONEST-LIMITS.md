# finance-captain — honest limits

## 1. It is not a CPA, an auditor, or an adviser

It does not give investment, tax, or securities advice, does not sign anything,
does not file anything, and does not provide assurance. Financial statements it
produces are management's, not an accountant's work product. Anything with tax
or securities consequence goes to a licensed professional.

## 2. The number fence is strong but bounded

The fence blocks unsourced numbers and — more usefully — numbers that do not
match the figure they cite, which catches stale copy-forward after data moved.
It does not catch:

- **A correctly cited figure computed from the wrong inputs.** If you feed
  `gross_margin` a COGS that omits hosting, you get a precise, traceable, wrong
  number. Provenance is not correctness.
- **A wrong COA mapping.** This is the most likely serious error in the whole
  profile, and nothing in code detects it. It is caught at onboarding by a human
  walking the account list, or it is not caught.
- **Prose that misrepresents a correct number.** "Revenue grew" attached to a
  valid figure that fell passes every gate.
- **Numbers inside images or charts** you did not generate from figures.

The fence can also fire on legitimate text — a quoted contract amount, a count
in a sentence. The fix is `[[EST: basis]]` or computing it properly. That
friction is intentional.

## 3. Snapshots are point-in-time, and the world is not

Accounting data is retroactively mutable. A snapshot is defensible because it is
pinned, not because it is current. `snapshot_diff` detects restatements only
between pulls you actually took; a change that happens between your last pull
and your reader's Tuesday is invisible.

## 4. Reconciliation is not the same as being right

A tie-out proves two totals agree. Two systems can agree and both be wrong —
a transaction categorized identically wrong in both ties perfectly.

## 5. Anomaly detection is signal, not conclusion

Duplicate flags are usually legitimate recurring charges. Outliers are usually
real large transactions. Benford means nothing on populations under a few
hundred or on data with fixed price points, and the tool refuses to report it
in those cases. **None of this is evidence of anything, and none of it should
be described to a person as a finding about their conduct.**

## 6. Forecasts are arithmetic, not prediction

`cash_forecast` rolls stated drivers forward deterministically. It has no view
on whether the drivers are right. Its output is exactly as good as the
assumptions, and its job is to make the assumptions explicit enough to argue with.

## 7. Writes are proposal-only by default, and should stay that way

`mutation_mode: propose_only` ships as the default. Turning on `approved_apply`
gives an agent the ability to write to your books. Even with approvals, caps,
and idempotency keys, understand the blast radius before you do it. Money
movement additionally requires a second explicit confirmation, and I would not
enable it at all.

The pipeline is defense in depth against error, not against a determined
adversary who controls the input data.

## 8. Security and confidentiality

- Snapshots, figures, and matter data sit in `plugin-data/fin/` in plaintext.
  Bank transactions, payroll, and customer names are in there. **No encryption,
  no access control.**
- Account-number redaction is a regex over tool output. It catches the common
  shapes and will miss unusual formats.
- Credentials should be read-only. A write-scoped Stripe key in an agent is a
  refund button; a write-scoped accounting token can restate your books.
- Sending financial data to a third-party model provider may violate an
  agreement or a policy you have. That is your call, not the tool's.

## 9. Uneven coverage

Metric definitions ship opinionated (SaaS-flavored: ARR, NRR, CAC). They are a
starting registry, not gospel — a services business, a marketplace, or anyone
with inventory needs definitions this registry does not have, and inventory
accounting in particular is absent. Multi-entity consolidation, eliminations,
revenue recognition under ASC 606, lease accounting, and equity accounting are
all out of scope: the profile will happily report on data that needed those
treatments and never applied them.

## 10. Unverified platform assumptions

Marked in `mcp.json` and `distribution.yaml`: the `hermes_requires` floor and
most MCP endpoints. Confirm or delete each at install. A missing server is
survivable — the CSV path works. A wrong scope on a credential is not.

## 11. What it is genuinely good at

Discipline. Pulling consistently, computing the same way every period, catching
the number that moved, refusing to publish something that does not tie, and
making every figure in a report traceable to the row it came from.
