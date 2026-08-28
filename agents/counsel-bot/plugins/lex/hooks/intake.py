"""Evidence intake: the retrieval payload never rides the window.

transform_tool_result fires after the tool returns and before the result is
appended to the conversation. We store the full text, sanitize it, and hand the
model a bounded authority card with a pointer back.
"""
from __future__ import annotations
import json, logging, re
from ..store import bus, ledger as L, matter as M, sanitize
from ..runtime import data_dir

log = logging.getLogger("lex.intake")
RETRIEVAL_TOOLS = {"web_extract", "web_search", "browser_snapshot", "browser_navigate",
                   "read_file", "vision_analyze"}
BIG = 6000


def _audit(kind: str, payload: dict) -> None:
    try:
        p = data_dir() / "audit" / "intake.jsonl"
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": kind, **payload}, default=str) + "\n")
    except Exception:
        pass


def transform_tool_result(tool_name=None, args=None, result=None, **kwargs):
    try:
        if tool_name not in RETRIEVAL_TOOLS or not isinstance(result, str):
            return None
        if len(result) < BIG:
            return None
        url = (args or {}).get("url") or (args or {}).get("path") or ""
        clean, suppressed = sanitize.clean(result)
        if suppressed:
            _audit("suppressed", {"url": url, "items": suppressed})

        m = M.load()
        row = L.add({"kind": "secondary", "url": url,
                     "title": _title(clean) or url[:120],
                     "jurisdiction": (m or {}).get("jurisdiction"),
                     "origin": f"tool:{tool_name}", "tier": "C",
                     "matter_id": (m or {}).get("matter_id")}, text=clean)
        card = L.card(row, spans=_spans(clean))
        card["source_tool"] = tool_name
        card["suppressed_instruction_blocks"] = len(suppressed)
        card["notice"] = (sanitize.WRAPPER.strip() +
                          " Full text stored; quote only via authority_read. "
                          "This is a retrieved web document, not verified primary law — "
                          "if you intend to cite it, register the underlying primary "
                          "source with authority_add.")
        _audit("card", {"auth": row["id"], "bytes": row.get("bytes"), "tool": tool_name})
        return json.dumps(card, default=str)
    except Exception:
        log.exception("intake failed; passing original result through")
        return None  # fail open, always


def _title(text: str) -> str | None:
    for line in text.splitlines():
        s = line.strip()
        if 10 < len(s) < 160:
            return s
    return None


def _spans(text: str, n: int = 3) -> list:
    """Deterministic first-pass spans: sentences that look operative."""
    KEY = re.compile(r"(?i)\b(shall|must|held that|we conclude|it is ordered|"
                     r"the term .* means|is defined as|provided that)\b")
    out = []
    for s in re.split(r"(?<=[.])\s+", text):
        s = re.sub(r"\s+", " ", s).strip()
        if KEY.search(s) and 40 < len(s) < 320:
            i = text.find(s[:40])
            out.append({"q": s[:240], "off": max(i, 0), "len": len(s)})
        if len(out) >= n:
            break
    return out


def transform_terminal_output(command=None, output=None, **kwargs):
    """Collapse huge fetch dumps before the terminal cap mangles them."""
    try:
        if not output or len(output) < 20000:
            return None
        if not any(k in (command or "") for k in ("curl", "wget", "cat ", "pdftotext")):
            return None
        rec = bus.store(output, {"origin": "terminal", "command": (command or "")[:200]})
        head = "\n".join(output.splitlines()[:40])
        return (f"{head}\n\n[lex: {len(output)} chars stored at {rec['path']} "
                f"(sha {rec['sha'][:12]}). Read slices with read_file offset/limit, "
                f"or register it with authority_add.]")
    except Exception:
        return None
