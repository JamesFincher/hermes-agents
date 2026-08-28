"""Flat, model-facing schemas."""
HATS = ["controller", "fpa", "treasury", "ar-ap", "investor-reporting", "bookkeeping"]
SOURCES = ["quickbooks", "xero", "stripe", "plaid", "ramp", "gsheets", "warehouse"]

DESCRIPTIONS = {
 "entity_open": "Open, switch, or inspect the entity whose books you are working on. Sets currency, accounting basis, fiscal calendar, and connected systems. Required before anything else.",
 "period_manage": "Manage an accounting period: status, close-checklist items, close, reopen. A final report requires a closed period.",
 "snapshot_pull": "Pull an immutable, timestamped snapshot from a connected system. Rows are stored, not returned. Every published number traces back to a snapshot.",
 "snapshot_diff": "Diff two snapshots of the same source and period to detect restatements — data that moved after you published on it.",
 "ledger_query": "Aggregate over a stored snapshot with filters and grouping. Returns totals and groups, not raw rows.",
 "metric_registry": "The entity's metric definitions with versions and formulas. One definition per metric, ever.",
 "metric_compute": "Compute a registered metric from named inputs. Returns a [F#] figure id you must cite when you use the number.",
 "budget_manage": "Get or set budget lines for a period.",
 "variance_report": "Actual vs budget by account, with materiality flagging and a figure id per material line.",
 "cash_forecast": "Deterministic driver-based cash roll-forward. Returns the month cash goes negative, if it does.",
 "anomaly_scan": "Deterministic exception scan over a snapshot: duplicates, outliers, uncategorized, suspicious round numbers, weekend entries, Benford shape.",
 "recon_tieout": "Reconcile two snapshots, or reconcile report totals against a snapshot. An unexplained difference is an open item, never a plug.",
 "figure_check": "Inspect a figure's provenance, or list every figure backing a period.",
 "report_scaffold": "Required sections, required figures, and the tie-out for a report type under the active hat.",
 "report_check": "Run the gates on a draft report without writing it: number fence, tie-out, freshness, metric definitions, required sections.",
 "mutation_propose": "Propose a write to a system of record — the only way to change anything. Produces a dry run and a proposal id for human approval.",
 "mutation_apply": "Execute a proposal after explicit human approval of that specific proposal id. Idempotent.",
 "audit_trail": "Read the audit log: gate decisions, snapshots, mutations, delegations.",
}

_period = {"type": "string", "description": "Accounting period, e.g. '2026-07' or '2026-Q3'."}

SCHEMAS = {
 "entity_open": {"type": "object", "properties": {
   "action": {"type": "string", "enum": ["open", "switch", "status", "set_hat"], "default": "open"},
   "name": {"type": "string"},
   "home_currency": {"type": "string", "default": "USD"},
   "basis": {"type": "string", "enum": ["cash", "accrual"],
             "description": "Required. Every number downstream means something different depending on this."},
   "fiscal_year_end": {"type": "string", "description": "MM-DD, e.g. 12-31."},
   "systems": {"type": "object", "description": "e.g. {\"accounting\":\"quickbooks\",\"banking\":\"plaid\"}"},
   "hat": {"type": "string", "enum": HATS},
   "entity_id": {"type": "string"}}, "required": ["action"]},

 "period_manage": {"type": "object", "properties": {
   "action": {"type": "string", "enum": ["status", "check", "close", "reopen"], "default": "status"},
   "period": _period, "item": {"type": "string", "description": "A close-checklist item id."},
   "done": {"type": "boolean", "default": True},
   "force": {"type": "boolean", "default": False},
   "reason": {"type": "string"}}, "required": ["action"]},

 "snapshot_pull": {"type": "object", "properties": {
   "source": {"type": "string", "enum": SOURCES},
   "kind": {"type": "string", "enum": ["transactions", "balances", "invoices", "bills",
                                       "payroll", "trial_balance", "ar_aging", "ap_aging"],
            "default": "transactions"},
   "period": _period, "start": {"type": "string"}, "end": {"type": "string"},
   "account": {"type": "string"}, "mcp_tool": {"type": "string"},
   "limit": {"type": "integer", "default": 5000}}, "required": ["source"]},

 "snapshot_diff": {"type": "object", "properties": {
   "old": {"type": "string"}, "new": {"type": "string"},
   "key": {"type": "string", "default": "id"}}, "required": ["old", "new"]},

 "ledger_query": {"type": "object", "properties": {
   "snapshot": {"type": "string"},
   "filters": {"type": "object", "properties": {
      "account": {"type": "string"}, "vendor": {"type": "string"},
      "date_from": {"type": "string"}, "date_to": {"type": "string"},
      "min_cents": {"type": "integer"}, "type": {"type": "string"}}},
   "group_by": {"type": "string", "enum": ["account", "vendor", "type", "date", "source"]},
   "include_rows": {"type": "boolean", "default": False},
   "limit": {"type": "integer", "default": 40}}, "required": ["snapshot"]},

 "metric_registry": {"type": "object", "properties": {"metric": {"type": "string"}}, "required": []},

 "metric_compute": {"type": "object", "properties": {
   "metric": {"type": "string"},
   "inputs": {"type": "object", "description": "Named inputs in CENTS for money values. Call metric_registry to see what each metric requires."},
   "period": _period,
   "snapshots": {"type": "array", "items": {"type": "string"},
                 "description": "The snapshot ids the inputs came from. Provenance."}},
   "required": ["metric", "inputs"]},

 "budget_manage": {"type": "object", "properties": {
   "action": {"type": "string", "enum": ["get", "set"], "default": "get"},
   "period": _period,
   "lines": {"type": "array", "items": {"type": "object", "properties": {
      "account": {"type": "string"}, "amount": {"type": "string"}, "note": {"type": "string"}}}}},
   "required": ["action"]},

 "variance_report": {"type": "object", "properties": {
   "period": _period, "snapshot": {"type": "string"},
   "actuals": {"type": "object", "description": "Optional {account: amount} if not from a snapshot."},
   "materiality_cents": {"type": "integer"}}, "required": ["period"]},

 "cash_forecast": {"type": "object", "properties": {
   "opening_cash": {"type": "string"}, "months": {"type": "integer", "default": 12},
   "drivers": {"type": "object", "properties": {
      "revenue_cents": {"type": "array", "items": {"type": "integer"}},
      "opex_cents": {"type": "array", "items": {"type": "integer"}},
      "cogs_pct": {"type": "number"},
      "collections_lag_months": {"type": "integer"}}},
   "snapshots": {"type": "array", "items": {"type": "string"}},
   "period": _period}, "required": ["opening_cash", "drivers"]},

 "anomaly_scan": {"type": "object", "properties": {
   "snapshot": {"type": "string"}, "z": {"type": "number"},
   "materiality_cents": {"type": "integer"}}, "required": ["snapshot"]},

 "recon_tieout": {"type": "object", "properties": {
   "snapshot_a": {"type": "string"}, "snapshot_b": {"type": "string"},
   "report_totals": {"type": "object"}, "snapshot": {"type": "string"},
   "tolerance_cents": {"type": "integer"}}, "required": []},

 "figure_check": {"type": "object", "properties": {
   "figure": {"type": "string"}, "period": _period}, "required": []},

 "report_scaffold": {"type": "object", "properties": {
   "report_type": {"type": "string", "description": "Call with '?' to list what this hat allows."},
   "period": _period}, "required": ["report_type"]},

 "report_check": {"type": "object", "properties": {
   "text": {"type": "string"}, "path": {"type": "string"},
   "report_type": {"type": "string"}, "period": _period,
   "snapshots": {"type": "array", "items": {"type": "string"}},
   "report_totals": {"type": "object", "description": "{label: amount} to tie against tie_to."},
   "tie_to": {"type": "string", "description": "Snapshot id the totals must reconcile to."},
   "final": {"type": "boolean", "default": False}}, "required": []},

 "mutation_propose": {"type": "object", "properties": {
   "system": {"type": "string", "enum": SOURCES},
   "action": {"type": "string", "description": "e.g. categorize_transaction, create_invoice, pay_bill."},
   "payload": {"type": "object"},
   "amount": {"type": "string"},
   "rationale": {"type": "string", "description": "Required. Why this write, in one sentence."},
   "dry_run_tool": {"type": "string"}}, "required": ["system", "action", "rationale"]},

 "mutation_apply": {"type": "object", "properties": {
   "proposal": {"type": "string"},
   "approved_by": {"type": "string", "description": "The human who approved THIS proposal id."},
   "confirm_money_movement": {"type": "boolean", "default": False}}, "required": ["proposal"]},

 "audit_trail": {"type": "object", "properties": {
   "stream": {"type": "string", "enum": ["policy", "mutations", "snapshots", "tools", "delegation"],
              "default": "policy"},
   "n": {"type": "integer", "default": 50}}, "required": []},
}
