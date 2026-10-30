from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.ids import new_id
from app.core.pipeline import detect_current, eval_rules, load_rules
from app.core.session_store import get_working_set
from app.db import get_db
from app.errors import AppError
from app.llm.templates import parse_nl_rule
from app.rules.evaluator import evaluate_rule
from app.rules.models import parse_rule, summarize
from app.rules.suggestions import suggest_rules

router = APIRouter()


@router.get("/sessions/{sid}/rules")
def list_rules(sid: str):
    db = get_db()
    rows = db.execute("SELECT * FROM rules WHERE session_id=?", (sid,)).fetchall()
    ws = get_working_set(sid)
    items = []
    for r in rows:
        rule = parse_rule(json.loads(r["json"]))
        res = evaluate_rule(ws.df, rule, ws.config.dayfirst_default)
        items.append({**dict(r), "rule": rule.model_dump(), "summary": summarize(rule), "result": {k: res[k] for k in ("violations", "unevaluable", "passed")}})
    return {"items": items}


@router.post("/sessions/{sid}/rules")
def add_rule(sid: str, body: dict):
    body = dict(body)
    body.setdefault("id", new_id(8))
    body.setdefault("name", body.get("name") or body.get("type", "rule"))
    rule = parse_rule(body)
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "INSERT INTO rules (id, session_id, name, enabled, json, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (rule.id, sid, rule.name, 1 if rule.enabled else 0, json.dumps(rule.model_dump()), now, now),
    )
    db.commit()
    get_working_set(sid).cache.clear()
    return {"rule": rule.model_dump()}


@router.put("/sessions/{sid}/rules/{rid}")
def update_rule(sid: str, rid: str, body: dict):
    body["id"] = rid
    rule = parse_rule(body)
    db = get_db()
    db.execute(
        "UPDATE rules SET name=?, enabled=?, json=?, updated_at=? WHERE id=? AND session_id=?",
        (rule.name, 1 if rule.enabled else 0, json.dumps(rule.model_dump()), datetime.now(timezone.utc).isoformat(), rid, sid),
    )
    db.commit()
    get_working_set(sid).cache.clear()
    return {"rule": rule.model_dump()}


@router.delete("/sessions/{sid}/rules/{rid}")
def delete_rule(sid: str, rid: str):
    db = get_db()
    db.execute("DELETE FROM rules WHERE id=? AND session_id=?", (rid, sid))
    db.commit()
    get_working_set(sid).cache.clear()
    return {"ok": True}


@router.post("/sessions/{sid}/rules/test")
def test_rule(sid: str, body: dict):
    body.setdefault("id", "tmp")
    body.setdefault("name", "test")
    rule = parse_rule(body)
    ws = get_working_set(sid)
    res = evaluate_rule(ws.df, rule, ws.config.dayfirst_default)
    reasons = list(res["reasons"].items())[:10]
    return {
        "violations": res["violations"],
        "unevaluable": res["unevaluable"],
        "passed": res["passed"],
        "preview": [{"rid": r, "reason": msg} for r, msg in reasons],
    }


@router.post("/sessions/{sid}/rules/run")
def run_all(sid: str):
    ws = get_working_set(sid)
    results = eval_rules(ws.df, load_rules(sid), ws.config.dayfirst_default)
    return {"items": [{k: r[k] for k in ("rule", "violations", "unevaluable", "passed", "summary")} for r in results]}


@router.get("/sessions/{sid}/rules/{rid}/violations")
def violations(sid: str, rid: str, offset: int = 0, limit: int = 50):
    ws = get_working_set(sid)
    rules = [r for r in load_rules(sid) if r.id == rid]
    if not rules:
        raise AppError("VALIDATION_ERROR", "Unknown rule.", "")
    res = evaluate_rule(ws.df, rules[0], ws.config.dayfirst_default)
    rids = res["rids"][offset : offset + limit]
    items = [{"rid": r, "row_number": r + 1, "reason": res["reasons"].get(r, ""), "values": {c: str(ws.df.at[r, c]) for c in res["columns"] if c in ws.df.columns}} for r in rids]
    return {"items": items, "total": len(res["rids"]), "unevaluable": res["unevaluable"]}


@router.get("/sessions/{sid}/suggested-rules")
def suggestions(sid: str):
    ws = get_working_set(sid)
    from app.profiling.profiler import profile_dataframe

    metas = profile_dataframe(ws.df, ws.config)["column_meta"]
    return {"items": suggest_rules(ws.df, metas, ws.config.dayfirst_default)}


@router.post("/sessions/{sid}/rules/from-text")
def from_text(sid: str, body: dict):
    ws = get_working_set(sid)
    parsed = parse_nl_rule(body.get("text") or "", list(ws.df.columns))
    if not parsed:
        raise AppError("VALIDATION_ERROR", "Couldn't understand — try the rule builder.", "")
    parsed.setdefault("id", new_id(8))
    parsed.setdefault("origin", "ai")
    rule = parse_rule(parsed)
    return {"source": "template", "rule": rule.model_dump()}


@router.get("/sessions/{sid}/rules-export")
def export_rules(sid: str):
    rules = [r.model_dump() for r in load_rules(sid)]
    return {"rules": rules}


@router.put("/sessions/{sid}/rules/import")
def import_rules(sid: str, body: dict):
    for item in body.get("rules") or []:
        item.setdefault("id", new_id(8))
        add_rule(sid, item)
    return {"ok": True}
