"""Keep raw financial data out of the window.

A transaction export is thousands of rows the model will never read carefully
and will re-read on every subsequent turn after compaction. It goes to the
snapshot store; the model gets a shape summary and queries it.
"""
from __future__ import annotations
import json, logging, re
from ..store import snapshot as S, money, audit
from ..runtime import data_dir, setting

log = logging.getLogger("fin.intake")
BIG = 6000
ACCT = re.compile(r"\b(?:\d[ -]?){12,19}\b")          # card/account-ish
ROUTING = re.compile(r"\b\d{9}\b")


def _redact(text: str) -> tuple[str, int]:
    if not setting("redact_account_numbers", True):
        return text, 0
    n = 0

    def sub(m):
        nonlocal n
        n += 1
        s = re.sub(r"\D", "", m.group(0))
        return f"[acct ****{s[-4:]}]"
    out = ACCT.sub(sub, text)
    return out, n


def transform_tool_result(tool_name=None, args=None, result=None, **kwargs):
    try:
        if not isinstance(result, str) or len(result) < BIG:
            return None
        if tool_name not in ("read_file", "web_extract", "terminal", "execute_code",
                             "browser_snapshot", "vision_analyze"):
            return None
        red, n = _redact(result)
        if n:
            audit.write("policy", {"event": "redacted_account_numbers", "count": n,
                                   "tool": tool_name})
        # Large tabular payloads get shape, not content.
        lines = red.splitlines()
        if len(lines) > 60 and ("," in red[:2000] or "\t" in red[:2000]):
            head = "\n".join(lines[:12])
            return json.dumps({
                "shape": {"lines": len(lines), "chars": len(red)},
                "head": head,
                "notice": "Large tabular payload. Rows were NOT loaded into context. "
                          "Load it as a snapshot (snapshot_pull source=gsheets, or "
                          "scripts/load_csv.py) and query it with ledger_query. "
                          "Do not read totals off this preview — they are not a snapshot "
                          "and cannot back a [F#].",
                "redacted_account_numbers": n}, default=str)
        if n:
            return red
        return None
    except Exception:
        log.exception("intake failed; passing through")
        return None


def transform_terminal_output(command=None, output=None, **kwargs):
    try:
        if not output or len(output) < 15000:
            return None
        red, n = _redact(output)
        head = "\n".join(red.splitlines()[:40])
        return (f"{head}\n\n[fin: {len(output)} chars truncated. If this is financial data, "
                f"load it as a snapshot instead of reading it here. Redacted {n} account numbers.]")
    except Exception:
        return None
