# hdr plugin

This plugin registers HDR tools and hooks on toolset `hdr`.
Skills live in the profile `skills/` directory. Do not register them here.

## scripts/

Four scripts are twins of skill copies. CI checks they stay byte-identical:

- `dedupe_urls.py`
- `crossref.py`
- `unpaywall.py`
- `pdf_text.py`

`timeline.py` sorts lines of the form `YYYY-MM-DD<TAB>event`.
No skill recipe calls it. Use it from the terminal when you need a dated sort.
It is not a sixth skill.
