"""Source tiering. Heuristic over domains and metadata. Not proof."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from ..runtime import setting

PRIMARY_HINTS = (
    "spec",
    "rfc",
    "doi.org",
    "arxiv.org",
    "gov",
    "edu",
    "docs.",
    "developer.",
    "legislation",
    "sec.gov",
)
TIER_A_HOSTS = {
    "arxiv.org",
    "doi.org",
    "nature.com",
    "science.org",
    "nih.gov",
    "who.int",
    "europa.eu",
    "sec.gov",
    "nist.gov",
    "ietf.org",
    "w3.org",
    "nousresearch.com",
    "hermes-agent.nousresearch.com",
}
TIER_B_HOSTS = {
    "nytimes.com",
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "theguardian.com",
    "washingtonpost.com",
    "ft.com",
}


def recency_bucket(published: Any) -> str:
    raw = str(published or "").strip()
    if len(raw) < 4 or not raw[:4].isdigit():
        return ""
    try:
        year = int(raw[:4])
        month = int(raw[5:7]) if len(raw) >= 7 and raw[5:7].isdigit() else 1
        day = int(raw[8:10]) if len(raw) >= 10 and raw[8:10].isdigit() else 1
        published_at = datetime(year, month, day, tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return ""
    days = (datetime.now(timezone.utc) - published_at).days
    if days < 365:
        return "recency:recent"
    if days < 365 * 5:
        return "recency:aging"
    return "recency:historical"


def _with_recency(row: dict[str, str], meta: dict[str, Any]) -> dict[str, str]:
    note = recency_bucket(meta.get("published"))
    if note:
        reason = row.get("tier_reason") or ""
        row["tier_reason"] = f"{reason}; {note}" if reason else note
    return row


def score_source(url: str, meta: dict[str, Any] | None = None) -> dict[str, str]:
    meta = meta or {}
    host = (urlparse(url).hostname or "").lower()
    overrides = setting("domain_tier_overrides", {}) or {}
    if isinstance(overrides, dict) and host in overrides:
        return _with_recency(
            {"tier": str(overrides[host]), "kind": "secondary", "tier_reason": "override"},
            meta,
        )
    if meta.get("doi") or "arxiv.org" in host:
        return _with_recency({"tier": "A", "kind": "primary", "tier_reason": "peer-reviewed"}, meta)
    if host in TIER_A_HOSTS or any(host.endswith("." + h) for h in TIER_A_HOSTS):
        return _with_recency({"tier": "A", "kind": "primary", "tier_reason": "first-party"}, meta)
    if any(hint in url.lower() for hint in PRIMARY_HINTS):
        return _with_recency({"tier": "A", "kind": "primary", "tier_reason": "first-party"}, meta)
    if host in TIER_B_HOSTS or any(host.endswith("." + h) for h in TIER_B_HOSTS):
        return _with_recency({"tier": "B", "kind": "secondary", "tier_reason": "major-outlet"}, meta)
    if host.endswith(".gov") or host.endswith(".edu"):
        return _with_recency({"tier": "A", "kind": "primary", "tier_reason": "first-party"}, meta)
    if "blog" in host or "medium.com" in host or "substack.com" in host:
        return _with_recency({"tier": "D", "kind": "tertiary", "tier_reason": "blog"}, meta)
    return _with_recency({"tier": "C", "kind": "secondary", "tier_reason": "unclassified"}, meta)
