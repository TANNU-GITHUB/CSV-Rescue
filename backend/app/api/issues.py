from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import unquote

from fastapi import APIRouter

from app.core.pipeline import detect_current
from app.core.session_store import get_working_set
from app.db import get_db

router = APIRouter()


@router.get("/sessions/{sid}/issues")
def list_issues(sid: str, type: str | None = None, column: str | None = None, status: str = "open", severity: str | None = None, q: str = ""):
    groups, _ = detect_current(sid)
    items = []
    for g in groups:
        if type and g.type != type:
            continue
        if column and g.column != column:
            continue
        if status and status != "all" and g.status != status:
            continue
        if severity and g.severity != severity:
            continue
        if q and q.lower() not in (g.reason + (g.column or "")).lower():
            continue
        d = g.model_dump()
        d["rids"] = d["rids"][:50]
        items.append(d)
    return {"items": items, "total": len(items)}


@router.get("/sessions/{sid}/issues/{key}/rows")
def issue_rows(sid: str, key: str, offset: int = 0, limit: int = 50):
    key = unquote(key)
    groups, _ = detect_current(sid)
    ws = get_working_set(sid)
    g = next((x for x in groups if x.key == key), None)
    if not g:
        return {"rows": [], "total": 0}
    rids = g.rids[offset : offset + limit]
    rows = []
    for rid in rids:
        rows.append({"rid": rid, "row_number": rid + 1, "cells": {c: str(ws.df.at[rid, c]) for c in ws.df.columns}})
    return {"rows": rows, "total": len(g.rids), "columns": list(ws.df.columns)}


@router.post("/sessions/{sid}/issues/{key}/dismiss")
def dismiss(sid: str, key: str, body: dict | None = None):
    key = unquote(key)
    groups, _ = detect_current(sid)
    g = next((x for x in groups if x.key == key), None)
    rids = g.rids if g else []
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO dismissals (session_id, issue_key, reason, rids_json, created_at) VALUES (?,?,?,?,?)",
        (sid, key, (body or {}).get("reason"), json.dumps(rids), datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    ws = get_working_set(sid)
    ws.cache.clear()
    return {"ok": True}


@router.post("/sessions/{sid}/issues/{key}/reopen")
def reopen(sid: str, key: str):
    key = unquote(key)
    db = get_db()
    db.execute("DELETE FROM dismissals WHERE session_id=? AND issue_key=?", (sid, key))
    db.commit()
    get_working_set(sid).cache.clear()
    return {"ok": True}
