# counsel-bot — honest limits

Read this before using the profile for anything real.

## 1. It is not a lawyer and cannot become one

No configuration of this profile creates an attorney-client relationship,
provides legal advice, or substitutes for a licensed attorney in the relevant
jurisdiction. Practicing law without a license is a crime in every US
jurisdiction. This is an instrument that produces reviewable work product.

If you are a lawyer: this is a drafting assistant whose output you own and must
verify. If you are not: the output is a starting point to take to a lawyer, a
court self-help center, or a legal aid organization.

## 2. "Never hallucinate" is enforced, not guaranteed

The gates make the common failures *refuse to be written*, which is much
stronger than prompting. They do not make the model incapable of being wrong.
Specifically:

- **The citation gate proves existence, not support.** A real case, correctly
  cited, attached to a proposition it does not support, passes the gate. Only
  reading the opinion catches that. The skills tell the agent to read; nothing
  in code forces it to understand.
- **The fact fence catches patterned particulars** — money, dates, dockets,
  addresses, durations, entity suffixes. It will miss an invented particular
  that does not match a pattern (a fabricated job title, an invented contract
  section number in prose form).
- **The fence can also fire on legitimate text**, e.g. a date quoted from an
  authority. The fix is to record it as a fact with its source. That friction
  is intentional.
- **Prose can be wrong without containing a citation or a particular.** A
  mischaracterized legal standard in a sentence with a valid citation attached
  passes every gate.
- **Regex citation extraction is a fallback.** Install `eyecite` in the
  execution environment for real parsing. Without it, unusual reporters and
  statutory forms may be missed by the extractor and therefore never checked.

## 3. Verification depends on services we do not control

- Without `COURTLISTENER_TOKEN`, external citation verification is unavailable.
  The profile reports citations as *unverified* rather than silently trusting
  them, but unverified is a weaker state than verified.
- The treatment check is a **citing-opinion count**. It is not Shepard's, not
  KeyCite, and not a validity signal. A case can be overruled and still have a
  high citation count. Negative treatment must be read, not inferred.
- Two of the three MCP endpoints in `mcp.json` are marked UNVERIFIED. Confirm
  or delete them at install; the eCFR path in `scripts/fetch_authority.py` is
  the supported fallback.

## 4. Coverage is uneven across US law

- Federal case law coverage is good. State trial court coverage is thin
  everywhere and effectively absent in many jurisdictions.
- State statutes and municipal codes have no uniform machine-readable source.
  Retrieval falls back to web extraction, and the as-of date is the retrieval
  date, not a publisher's currency guarantee.
- **Local rules, standing orders, and county-level requirements are the most
  common source of a rejected filing, and they are the least machine-accessible
  material in American law.** The profile tells the agent to retrieve them. It
  cannot guarantee it found the current version.
- Mandatory forms change edition frequently, especially in family, immigration,
  and probate practice. Always confirm the edition with the court.

## 5. Deadlines

`deadline_compute` refuses without a retrieved rule and applies **federal
holidays only**. It does not know local court holidays, standing orders,
emergency closures, mailbox-rule variations, or the dozens of jurisdiction
specific counting conventions. Every date it produces carries a caveat telling
you to confirm with the forum. Treat a computed date as a prompt to check, never
as the answer.

## 6. Domains where the profile should defer, not draft

Family, immigration, criminal, eviction with a hearing date, and protective
orders. The consequences of an error are personal and immediate, mandatory forms
usually govern, and the pro-se hat is instructed to lead with a referral. The
profile will still work in these areas; the instruction is that it should not be
the last reviewer.

## 7. Security and confidentiality

- Matter facts, authorities, and drafts persist in `plugin-data/lex/` in
  plaintext on the host. **There is no encryption, no access control, and no
  privilege protection.** Anything you put in a matter is readable by anyone
  with filesystem access.
- Retrieved web content is sanitized for common prompt-injection shapes and
  wrapped as untrusted data. That is defense in depth, not a proof. The Docker
  terminal backend is the boundary that actually matters — do not switch it to
  `local` without understanding that.
- Confidentiality obligations may prohibit sending client information to a
  third-party model provider at all. That is your call to make, not the tool's.

## 8. Unverified platform assumptions

Marked `[UNV]` in the spec and requiring a doc/code probe before you rely on them:
the `hermes_requires` floor, whether subagents resolve the same `HERMES_HOME`
(the ledger-sharing design in delegation depends on it), whether `pre_tool_call`
can block `delegate_task`, and the two MCP endpoints above.

## 9. What it is genuinely good at

Structure, completeness, and catching other people's fabricated citations.
Auditing a document produced by another AI system is the strongest use case in
the box: `cite-check` will find fabricated authority faster and more reliably
than a human skimming a brief.
