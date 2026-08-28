#!/usr/bin/env python3
"""Extract every citation from a file and check it against CourtListener's
citation-lookup endpoint — the service built specifically as a hallucination
guardrail. Prints JSON. Exit code 1 if anything is unresolved.

  python3 verify_citations.py drafts/motion.md
Env: COURTLISTENER_TOKEN
"""
import json, os, re, sys, urllib.parse, urllib.request

CASE = re.compile(r"\b(\d{1,4})\s+([A-Z][A-Za-z.'’]*(?:\s*[A-Z][A-Za-z.'’]*){0,4}\.?(?:\s?\d[dh]?)?)\s+(\d{1,5})\b")


def lookup(text, token):
    data = urllib.parse.urlencode({"text": text[:60000]}).encode()
    req = urllib.request.Request(
        "https://www.courtlistener.com/api/rest/v4/citation-lookup/",
        data=data, headers={"Authorization": f"Token {token}",
                            "User-Agent": "counsel-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: verify_citations.py <file>"})); sys.exit(2)
    text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    token = os.environ.get("COURTLISTENER_TOKEN")
    local = sorted({m.group(0) for m in CASE.finditer(text)})
    if not token:
        print(json.dumps({"local_citations": local, "verified": False,
                          "error": "COURTLISTENER_TOKEN not set — cannot verify. "
                                   "Treat every citation as unverified."})); sys.exit(1)
    try:
        res = lookup(text, token)
    except Exception as e:
        print(json.dumps({"local_citations": local, "verified": False,
                          "error": f"{type(e).__name__}: {e}"})); sys.exit(1)
    bad = [r for r in res if str(r.get("status")) != "200"]
    print(json.dumps({"checked": len(res), "unresolved": bad,
                      "resolved": [r.get("citation") for r in res if str(r.get("status")) == "200"]},
                     indent=2))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
