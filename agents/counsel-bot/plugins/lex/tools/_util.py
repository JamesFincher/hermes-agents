import functools, json, logging
log = logging.getLogger("lex.tools")


def tool(fn):
    """Every handler returns a json.dumps string, never a dict, and never raises."""
    @functools.wraps(fn)
    def wrapper(args, **kwargs):
        try:
            out = fn(args or {}, **kwargs)
        except Exception as e:  # noqa: BLE001
            log.exception("tool %s failed", fn.__name__)
            out = {"error": f"{type(e).__name__}: {e}", "tool": fn.__name__}
        try:
            return json.dumps(out, default=str)
        except Exception:
            return json.dumps({"error": "unserializable result", "tool": fn.__name__})
    return wrapper


def need_matter(m):
    if not m:
        return {"error": "No active matter. Call matter_open first — jurisdiction and "
                         "represented party gate every drafting tool."}
    return None
