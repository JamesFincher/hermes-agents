#!/usr/bin/env python3
"""Retrieve a primary-law document and print JSON for authority_add.

Deterministic fetch + text extraction so the model never writes an ad-hoc
parser. Supports CourtListener opinions, eCFR sections, and plain URLs.

  python3 fetch_authority.py --courtlistener 108713
  python3 fetch_authority.py --ecfr 29 785.11
  python3 fetch_authority.py --url https://... --kind statute
Env: COURTLISTENER_TOKEN (optional but strongly recommended)
"""
import argparse, json, os, re, sys, urllib.request, urllib.error

UA = {"User-Agent": "counsel-bot/1.0 (+lex plugin)"}


def get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def strip_html(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = re.sub(r"&nbsp;?", " ", h)
    return re.sub(r"[ \t]+\n", "\n", re.sub(r"[ \t]{2,}", " ", h)).strip()


def courtlistener(opinion_id):
    tok = os.environ.get("COURTLISTENER_TOKEN")
    hdr = {"Authorization": f"Token {tok}"} if tok else {}
    o = json.loads(get(f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/", hdr))
    text = o.get("plain_text") or strip_html(o.get("html_with_citations") or o.get("html") or "")
    cluster = {}
    if o.get("cluster"):
        try:
            cluster = json.loads(get(o["cluster"], hdr))
        except Exception:
            pass
    return {"kind": "case", "title": cluster.get("case_name"),
            "citation": (cluster.get("citations") or [{}])[0].get("cite") if cluster.get("citations") else None,
            "date": cluster.get("date_filed"),
            "url": "https://www.courtlistener.com" + (cluster.get("absolute_url") or ""),
            "text": text}


def ecfr(title, section):
    url = f"https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/title-{title}?part={section.split('.')[0]}"
    body = strip_html(get(url))
    return {"kind": "regulation", "citation": f"{title} C.F.R. § {section}",
            "title": f"{title} CFR {section}", "url": url, "text": body,
            "as_of": __import__("datetime").date.today().isoformat()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--courtlistener"); ap.add_argument("--ecfr", nargs=2)
    ap.add_argument("--url"); ap.add_argument("--kind", default="secondary")
    a = ap.parse_args()
    try:
        if a.courtlistener:
            out = courtlistener(a.courtlistener)
        elif a.ecfr:
            out = ecfr(a.ecfr[0], a.ecfr[1])
        elif a.url:
            out = {"kind": a.kind, "url": a.url, "text": strip_html(get(a.url))}
        else:
            ap.error("pick a source")
        out["chars"] = len(out.get("text") or "")
        print(json.dumps(out)[:200000])
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"HTTP {e.code}", "hint":
              "CourtListener API access requires a token/membership; set COURTLISTENER_TOKEN"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"})); sys.exit(1)


if __name__ == "__main__":
    main()
