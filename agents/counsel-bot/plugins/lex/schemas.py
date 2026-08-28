"""Flat, model-facing schemas. Every field the model sees is here and nowhere else."""

HATS = ["litigation", "transactional", "corporate", "employment", "ip",
        "real-estate", "family", "immigration", "estates", "regulatory", "pro-se"]

DESCRIPTIONS = {
 "matter_open": "Open or switch the active matter. Establishes jurisdiction, forum, posture, and parties. Required before any drafting tool will run.",
 "matter_fact": "Record, list, or retract a fact for the active matter. Only recorded facts may appear in a draft as concrete particulars; everything else must be a [[FACT:...]] placeholder.",
 "set_hat": "Set the practice hat for the active matter. Gates which document types, checklists, and authority sources are available.",
 "authority_search": "Search primary law (cases, statutes, regulations, court rules) for the active jurisdiction. Returns authority cards, never full text.",
 "authority_add": "Register an authority you retrieved yourself (uploaded PDF, terminal fetch, exhibit). Auto-registration normally happens on retrieval.",
 "authority_read": "Return a byte range of a stored authority's full text. The only sanctioned way to bring primary-source text back into context.",
 "authority_status": "Currency and treatment check for one authority: as-of date, staleness, citing opinions, negative-treatment signals.",
 "cite_check": "Verify every citation in a block of text against the ledger and the citation-lookup service. Returns per-citation resolution status.",
 "cite_format": "Format ledger authorities into citations or a table of authorities in the configured format. The only sanctioned citation producer.",
 "conflict_report": "Every proposition in the ledger where authorities disagree, with jurisdiction, court level, and date.",
 "draft_scaffold": "Produce the required-elements skeleton for a document type under the active hat and jurisdiction, with [[FACT:...]] placeholders for every particular.",
 "draft_check": "Run the full gate set over a draft without writing it: citation gate, fact fence, jurisdiction fence, required elements, currency.",
 "deadline_compute": "Deterministically compute a date from a retrieved rule. Refuses without a rule authority id. Never estimates.",
 "issue_plan": "Decompose the matter into independently researchable legal issues with elements and the authority each would require.",
 "worker_brief": "Compile a self-contained brief for delegating one issue to a retrieval child, including its boundary and output contract.",
}

_matter_id = {"type": "string", "description": "Matter id from matter_open. Defaults to the active matter."}

SCHEMAS = {
 "matter_open": {"type": "object", "properties": {
    "action": {"type": "string", "enum": ["open", "switch", "status", "list"], "default": "open"},
    "name": {"type": "string"},
    "jurisdiction": {"type": "string", "description": "US-<STATE> or US-FED. e.g. US-CA, US-NY, US-FED."},
    "forum": {"type": "string", "description": "Specific court or agency, e.g. 'N.D. Cal.', 'Cal. Super. Ct. Alameda', 'USPTO', 'none'."},
    "posture": {"type": "string", "description": "e.g. pre-filing, pleading, discovery, motion practice, appeal, deal-negotiation, formation, compliance."},
    "parties": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string"}, "role": {"type": "string"}}}},
    "represented_party": {"type": "string", "description": "Whose side the work product is for. Required."},
    "matter_id": _matter_id}, "required": ["action"]},

 "matter_fact": {"type": "object", "properties": {
    "action": {"type": "string", "enum": ["add", "list", "retract"], "default": "add"},
    "key": {"type": "string", "description": "Stable slug, e.g. 'lease_start_date'."},
    "value": {"type": "string"},
    "source": {"type": "string", "description": "Where the fact came from: 'user', a document id, or an exhibit path. Required for add."},
    "matter_id": _matter_id}, "required": ["action"]},

 "set_hat": {"type": "object", "properties": {
    "hat": {"type": "string", "enum": HATS},
    "matter_id": _matter_id}, "required": ["hat"]},

 "authority_search": {"type": "object", "properties": {
    "query": {"type": "string"},
    "kind": {"type": "string", "enum": ["case", "statute", "regulation", "court_rule", "any"], "default": "any"},
    "jurisdiction": {"type": "string", "description": "Defaults to the matter's jurisdiction. Set explicitly to search persuasive authority."},
    "court": {"type": "string"},
    "date_after": {"type": "string"}, "date_before": {"type": "string"},
    "limit": {"type": "integer", "default": 8, "maximum": 25}}, "required": ["query"]},

 "authority_add": {"type": "object", "properties": {
    "kind": {"type": "string", "enum": ["case", "statute", "regulation", "court_rule", "secondary", "exhibit"]},
    "citation": {"type": "string"}, "title": {"type": "string"},
    "url": {"type": "string"}, "path": {"type": "string", "description": "Local file for uploaded exhibits or PDFs."},
    "jurisdiction": {"type": "string"}, "court": {"type": "string"},
    "date": {"type": "string"}, "as_of": {"type": "string"},
    "text": {"type": "string", "description": "Full text if you already have it. Stored to the corpus, not context."}},
    "required": ["kind"]},

 "authority_read": {"type": "object", "properties": {
    "auth_id": {"type": "string", "description": "e.g. A12"},
    "offset": {"type": "integer", "default": 0},
    "limit": {"type": "integer", "default": 4000, "maximum": 20000},
    "find": {"type": "string", "description": "Optional: jump to the first occurrence of this string."}},
    "required": ["auth_id"]},

 "authority_status": {"type": "object", "properties": {
    "auth_id": {"type": "string"}, "refresh": {"type": "boolean", "default": False}},
    "required": ["auth_id"]},

 "cite_check": {"type": "object", "properties": {
    "text": {"type": "string", "description": "The passage or draft to check."},
    "strict": {"type": "boolean", "default": True}}, "required": ["text"]},

 "cite_format": {"type": "object", "properties": {
    "auth_ids": {"type": "array", "items": {"type": "string"}},
    "style": {"type": "string", "enum": ["bluebook", "alwd", "plain"]},
    "mode": {"type": "string", "enum": ["inline", "full", "table_of_authorities"], "default": "full"},
    "short_form": {"type": "boolean", "default": False}}, "required": []},

 "conflict_report": {"type": "object", "properties": {
    "proposition": {"type": "string", "description": "Optional filter."},
    "matter_id": _matter_id}, "required": []},

 "draft_scaffold": {"type": "object", "properties": {
    "doc_type": {"type": "string", "description": "Registry key, e.g. 'complaint', 'msa', 'nda', 'motion_to_dismiss', 'operating_agreement', 'demand_letter'. Call with doc_type='?' to list what this hat allows."},
    "variant": {"type": "string"},
    "matter_id": _matter_id}, "required": ["doc_type"]},

 "draft_check": {"type": "object", "properties": {
    "text": {"type": "string"},
    "path": {"type": "string", "description": "Alternative to text: check a draft already on disk."},
    "doc_type": {"type": "string"}}, "required": []},

 "deadline_compute": {"type": "object", "properties": {
    "rule_auth_id": {"type": "string", "description": "Authority id of the retrieved rule that supplies the period. Required."},
    "trigger_date": {"type": "string", "description": "YYYY-MM-DD."},
    "period_days": {"type": "integer"},
    "day_type": {"type": "string", "enum": ["calendar", "court"], "default": "calendar"},
    "direction": {"type": "string", "enum": ["after", "before"], "default": "after"},
    "jurisdiction": {"type": "string"}},
    "required": ["rule_auth_id", "trigger_date", "period_days"]},

 "issue_plan": {"type": "object", "properties": {
    "action": {"type": "string", "enum": ["create", "update", "status"], "default": "create"},
    "issues": {"type": "array", "items": {"type": "object", "properties": {
        "question": {"type": "string"},
        "elements": {"type": "array", "items": {"type": "string"}},
        "authority_needed": {"type": "array", "items": {"type": "string"}}}}},
    "matter_id": _matter_id}, "required": ["action"]},

 "worker_brief": {"type": "object", "properties": {
    "issue_index": {"type": "integer"},
    "boundary": {"type": "string", "description": "What sibling workers are covering, so this one does not."},
    "max_fetches": {"type": "integer", "default": 10}}, "required": ["issue_index"]},
}
