"""URL canonicalization. Stdlib only so skill scripts can import it."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "amp",
    }
)
_DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
_ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", re.I)
_AMP_LAST = frozenset({"amp", "amp.html"})


def canonicalize(url: str) -> str:
    """Strip tracking, www, AMP, and unify http to https."""
    raw = (url or "").strip()
    if not raw:
        return ""
    doi = _DOI_RE.search(raw)
    if raw.lower().startswith("doi:") and doi:
        return f"https://doi.org/{doi.group(1)}"
    arxiv = _ARXIV_RE.search(raw)
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv.group(1)}"
    if "://" not in raw and raw.startswith("www."):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.scheme:
        return raw.rstrip("/")
    host = (parsed.hostname or "").lower()
    if host.startswith("m."):
        host = host[2:]
    if host.startswith("amp."):
        host = host[4:]
    if host.endswith(".ampproject.org"):
        host = host[: -len(".ampproject.org")]
    if host.startswith("www."):
        host = host[4:]
    scheme = parsed.scheme.lower()
    if scheme == "http":
        scheme = "https"
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in _TRACKING
    ]
    path = _amp_path(parsed.path or "")
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    return urlunparse(
        (
            scheme,
            host + (f":{parsed.port}" if parsed.port else ""),
            path,
            "",
            urlencode(query, doseq=True),
            "",
        )
    )


def _amp_path(path: str) -> str:
    segs = [part for part in path.split("/") if part]
    if segs and segs[0].lower() == "amp":
        segs = segs[1:]
    if segs and segs[-1].lower() in _AMP_LAST:
        segs = segs[:-1]
    if not segs:
        return "/"
    return "/" + "/".join(segs)
