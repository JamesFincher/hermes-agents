"""Deterministic metadata extraction: JSON-LD, OpenGraph, citation_*, DOI."""

from __future__ import annotations

import json
import re
from typing import Any

_DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
_OG_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\']og:([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_OG_RE_SWAP = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:([^"\']+)["\']',
    re.I,
)
_CITATION_RE = re.compile(
    r'<meta[^>]+name=["\']citation_([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_DATE_RE = re.compile(r"(20\d{2}|19\d{2})-\d{2}-\d{2}")
_REL_AUTHOR = re.compile(
    r'<a[^>]+rel=["\']author["\'][^>]*>(.*?)</a>',
    re.I | re.S,
)
_BYLINE = re.compile(
    r'<(?:span|div|p)[^>]+class=["\'][^"\']*\bbyline\b[^"\']*["\'][^>]*>(.*?)</(?:span|div|p)>',
    re.I | re.S,
)
_ITEMPROP_AUTHOR = re.compile(
    r'<[^>]+itemprop=["\']author["\'][^>]*>(.*?)</[^>]+>',
    re.I | re.S,
)
_META_AUTHOR = re.compile(
    r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_TAG_RE = re.compile(r"<[^>]+>")


def extract_metadata(html_or_text: str, url: str = "") -> dict[str, Any]:
    text = html_or_text or ""
    meta: dict[str, Any] = {
        "title": "",
        "authors": [],
        "publisher": "",
        "published": None,
        "doi": None,
        "arxiv": None,
    }
    doi = _DOI_RE.search(text) or _DOI_RE.search(url)
    if doi:
        meta["doi"] = doi.group(1)
    title_match = _TITLE_RE.search(text)
    if title_match:
        meta["title"] = re.sub(r"\s+", " ", title_match.group(1)).strip()
    for match in _OG_RE.finditer(text):
        key, value = match.group(1).lower(), match.group(2).strip()
        _apply_og(meta, key, value)
    for match in _OG_RE_SWAP.finditer(text):
        value, key = match.group(1).strip(), match.group(2).lower()
        _apply_og(meta, key, value)
    for match in _CITATION_RE.finditer(text):
        key, value = match.group(1).lower(), match.group(2).strip()
        if key == "title" and not meta["title"]:
            meta["title"] = value
        elif key in {"author", "authors"}:
            meta["authors"].append(value)
        elif key in {"publication_date", "date", "online_date"}:
            meta["published"] = value
        elif key == "doi" and not meta["doi"]:
            meta["doi"] = value
        elif key == "journal_title":
            meta["publisher"] = value
    for match in _JSONLD_RE.finditer(text):
        try:
            payload = json.loads(match.group(1))
        except Exception:
            continue
        _apply_jsonld(meta, payload)
    if not meta["published"]:
        date = _DATE_RE.search(text)
        if date:
            meta["published"] = date.group(0)
    if "arxiv.org" in url:
        arxiv = re.search(r"(\d{4}\.\d{4,5})", url)
        if arxiv:
            meta["arxiv"] = arxiv.group(1)
    _apply_byline(meta, text)
    meta["authors"] = list(dict.fromkeys(meta["authors"]))
    return meta


def _clean_name(value: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub("", value or "")).strip()


def _apply_byline(meta: dict[str, Any], text: str) -> None:
    for match in _META_AUTHOR.finditer(text):
        name = _clean_name(match.group(1))
        if name:
            meta["authors"].append(name)
    for pattern in (_REL_AUTHOR, _BYLINE, _ITEMPROP_AUTHOR):
        for match in pattern.finditer(text):
            name = _clean_name(match.group(1))
            if name:
                meta["authors"].append(name)


def _apply_og(meta: dict[str, Any], key: str, value: str) -> None:
    if key == "title" and not meta["title"]:
        meta["title"] = value
    elif key == "site_name" and not meta["publisher"]:
        meta["publisher"] = value
    elif key in {"article:published_time", "updated_time"} and not meta["published"]:
        meta["published"] = value[:10]


def _apply_jsonld(meta: dict[str, Any], payload: Any) -> None:
    nodes = payload if isinstance(payload, list) else [payload]
    graph = []
    for node in nodes:
        if isinstance(node, dict) and "@graph" in node:
            graph.extend(node.get("@graph") or [])
        elif isinstance(node, dict):
            graph.append(node)
    for node in graph:
        if not isinstance(node, dict):
            continue
        types = node.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if not any(
            str(item).lower() in {"article", "newsarticle", "scholarlyarticle", "webpage"}
            for item in type_list
        ):
            if not meta["title"] and node.get("name"):
                meta["title"] = str(node.get("name"))
            continue
        if node.get("headline") and not meta["title"]:
            meta["title"] = str(node["headline"])
        if node.get("datePublished") and not meta["published"]:
            meta["published"] = str(node["datePublished"])[:10]
        author = node.get("author")
        authors = author if isinstance(author, list) else [author]
        for item in authors:
            if isinstance(item, dict) and item.get("name"):
                meta["authors"].append(str(item["name"]))
            elif isinstance(item, str):
                meta["authors"].append(item)
        pub = node.get("publisher")
        if isinstance(pub, dict) and pub.get("name") and not meta["publisher"]:
            meta["publisher"] = str(pub["name"])
