#!/usr/bin/env python3
"""Deterministic redline between two drafts. Never ask a model to diff text.
  python3 redline.py old.md new.md [--format md|unified]
"""
import argparse, difflib, re, sys


def sentences(p):
    t = open(p, encoding="utf-8", errors="replace").read()
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n", t) if s.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old"); ap.add_argument("new"); ap.add_argument("--format", default="md")
    a = ap.parse_args()
    o, n = sentences(a.old), sentences(a.new)
    if a.format == "unified":
        sys.stdout.writelines(difflib.unified_diff(o, n, a.old, a.new, lineterm="\n"))
        return
    sm = difflib.SequenceMatcher(None, o, n)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag in ("replace", "delete"):
            for s in o[i1:i2]:
                print(f"~~{s}~~")
        if tag in ("replace", "insert"):
            for s in n[j1:j2]:
                print(f"**{s}**")
    print("\n<!-- redline generated deterministically; no model involved -->")


if __name__ == "__main__":
    main()
