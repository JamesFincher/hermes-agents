from __future__ import annotations
from ._util import tool, need_entity
from ..store import entity as E, mutations as MU, money, audit
from ..runtime import call_mcp, setting


@tool
def mutation_propose(args, **kw):
    """Nothing is written to a system of record without going through here first."""
    e = E.load()
    if (err := need_entity(e)):
        return err
    system, action = args.get("system"), args.get("action")
    payload = args.get("payload") or {}
    if not system or not action:
        return {"error": "system and action are required"}
    amount = None
    if args.get("amount") is not None or payload.get("amount") is not None:
        amount = money.to_cents(args.get("amount", payload.get("amount")))
    if not args.get("rationale"):
        return {"error": "rationale is required. A write nobody can explain is a write nobody approves."}

    dry = call_mcp(system, args.get("dry_run_tool", f"{action}_preview"),
                   {**payload, "dry_run": True})
    dry_result = dry.get("result") if dry.get("ok") else {"unavailable": dry.get("error")}

    p = MU.propose(system, action, payload, e["entity_id"], amount,
                   args["rationale"], dry_result)
    audit.write("mutations", {"event": "proposed", "id": p["id"], "system": system,
                              "action": action, "class": p["class"], "amount_cents": amount})
    return {"ok": True, "proposal": p["id"], "class": p["class"],
            "system": system, "action": action, "amount": p["amount"],
            "payload": payload, "dry_run": dry_result,
            "idempotency_key": p["idempotency_key"],
            "status": p["status"],
            "next": ("Show this proposal to the human in full — system, action, amount, and what "
                     "changes — and get an explicit yes for THIS proposal id. Then "
                     "mutation_apply. A general 'go ahead' from earlier in the conversation is "
                     "not approval for this.")}


@tool
def mutation_apply(args, **kw):
    pid = args.get("proposal")
    p = MU.get(pid)
    if not p:
        return {"error": f"no proposal {pid}"}
    if p["status"] == "applied":
        return {"ok": True, "already_applied": True, "proposal": pid, "result": p["result"],
                "note": "idempotent: this was already executed and was not repeated"}

    mode = str(setting("mutation_mode", "propose_only"))
    if mode == "propose_only":
        return {"error": "mutation_mode is propose_only — this profile cannot execute writes.",
                "proposal": pid,
                "how": "an operator applies it in the source system, or an administrator sets "
                       "plugins.entries.fin.settings.mutation_mode: approved_apply after "
                       "reviewing the blast radius."}

    approval = args.get("approval_token") or args.get("approved_by")
    if not approval:
        return {"error": "explicit approval is required", "proposal": pid,
                "required": "approved_by=<the human who said yes to this exact proposal>"}

    cap = int(setting("mutation_max_cents", 0))
    if p.get("amount_cents") and cap and abs(p["amount_cents"]) > cap:
        return {"error": f"amount {p['amount']} exceeds the configured mutation cap",
                "cap": money.fmt(cap), "proposal": pid}
    if p["class"] == "money_movement" and not args.get("confirm_money_movement"):
        return {"error": "money movement requires confirm_money_movement=true in addition to "
                         "approval. Two keys for the one action that cannot be undone.",
                "proposal": pid, "amount": p["amount"]}

    MU.approve(pid, approval)
    env = call_mcp(p["system"], p["action"],
                   {**p["payload"], "idempotency_key": p["idempotency_key"]})
    if not env.get("ok"):
        audit.write("mutations", {"event": "failed", "id": pid, "error": env.get("error")})
        return {"error": f"{p['system']} rejected the write: {env.get('error')}",
                "proposal": pid, "status": "approved_not_applied",
                "note": "the proposal stays approved and retryable under the same "
                        "idempotency key. Do not construct a second proposal."}
    MU.mark_applied(pid, env.get("result"))
    audit.write("mutations", {"event": "applied", "id": pid, "by": approval,
                              "system": p["system"], "action": p["action"],
                              "amount_cents": p.get("amount_cents")})
    return {"ok": True, "proposal": pid, "applied": True, "result": env.get("result"),
            "audit": "recorded in plugin-data/fin/audit/mutations.jsonl"}
