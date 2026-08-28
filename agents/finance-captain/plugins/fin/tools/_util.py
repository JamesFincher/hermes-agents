import functools, json, logging
log = logging.getLogger("fin.tools")


def tool(fn):
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


def need_entity(e):
    if not e:
        return {"error": "No active entity. Call entity_open first — currency, basis, and "
                         "fiscal calendar gate every computation."}
    return None
