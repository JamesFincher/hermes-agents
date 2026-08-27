"""Model-facing handlers. Each returns a json.dumps string."""

from .citation import claim_verify, cite_source, conflict_report
from .evidence import evidence_add, evidence_read, evidence_search, evidence_stats
from .fanout import worker_brief, worker_harvest
from .plan import gap_scan, research_plan
from .retrieval import archive_lookup, docs_query, resolve_library, scholar_search

__all__ = [
    "research_plan",
    "gap_scan",
    "evidence_add",
    "evidence_search",
    "evidence_read",
    "evidence_stats",
    "claim_verify",
    "conflict_report",
    "cite_source",
    "worker_brief",
    "worker_harvest",
    "resolve_library",
    "docs_query",
    "scholar_search",
    "archive_lookup",
]
