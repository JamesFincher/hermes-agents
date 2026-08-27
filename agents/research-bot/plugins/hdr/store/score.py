"""Source tiering. Heuristic over domains and metadata. Not proof."""

from __future__ import annotations

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


def score_source(url: str, meta: dict[str, Any] | None = None) -> dict[str, str]:
    meta = meta or {}
    host = (urlparse(url).hostname or "").lower()
    overrides = setting("domain_tier_overrides", {}) or {}
    if isinstance(overrides, dict) and host in overrides:
        return {"tier": str(overrides[host]), "kind": "secondary", "tier_reason": "override"}
    if meta.get("doi") or "arxiv.org" in host:
        return {"tier": "A", "kind": "primary", "tier_reason": "peer-reviewed"}
    if host in TIER_A_HOSTS or any(host.endswith("." + h) for h in TIER_A_HOSTS):
        return {"tier": "A", "kind": "primary", "tier_reason": "first-party"}
    if any(hint in url.lower() for hint in PRIMARY_HINTS):
        return {"tier": "A", "kind": "primary", "tier_reason": "first-party"}
    if host in TIER_B_HOSTS or any(host.endswith("." + h) for h in TIER_B_HOSTS):
        return {"tier": "B", "kind": "secondary", "tier_reason": "major-outlet"}
    if host.endswith(".gov") or host.endswith(".edu"):
        return {"tier": "A", "kind": "primary", "tier_reason": "first-party"}
    if "blog" in host or "medium.com" in host or "substack.com" in host:
        return {"tier": "D", "kind": "tertiary", "tier_reason": "blog"}
    return {"tier": "C", "kind": "secondary", "tier_reason": "unclassified"}
