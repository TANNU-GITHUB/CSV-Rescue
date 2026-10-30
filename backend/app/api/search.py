from __future__ import annotations

from fastapi import APIRouter

from app.core.pipeline import detect_current, load_rules, proposals_for
from app.core.session_store import get_working_set
from app.db import get_db

router = APIRouter()

PAGES = [
    {"id": "dashboard", "label": "Dashboard", "route": "/"},
    {"id": "datasets", "label": "Datasets", "route": "/datasets"},
    {"id": "profile", "label": "Profile", "route": "/profile"},
    {"id": "issues", "label": "Issues", "route": "/issues"},
    {"id": "studio", "label": "Cleaning Studio", "route": "/studio"},
    {"id": "rules", "label": "Rules", "route": "/rules"},
    {"id": "history", "label": "History", "route": "/history"},
    {"id": "reports", "label": "Reports", "route": "/reports"},
    {"id": "settings", "label": "Settings", "route": "/settings"},
]


@router.get("/sessions/{sid}/search")
def search(sid: str, q: str = ""):
    qn = q.strip().lower()
    ws = get_working_set(sid)
    pages = [p for p in PAGES if not qn or qn in p["label"].lower()]
    columns = [{"name": c} for c in ws.df.columns if not qn or qn in c.lower()]
    groups, _ = detect_current(sid)
    issues = [{"key": g.key, "reason": g.reason} for g in groups if not qn or qn in g.reason.lower() or qn in (g.column or "").lower()][:20]
    rules = [{"name": r.name, "id": r.id} for r in load_rules(sid) if not qn or qn in r.name.lower()]
    db = get_db()
    ops = db.execute("SELECT id, title FROM operations WHERE session_id=?", (sid,)).fetchall()
    history = [{"id": o["id"], "title": o["title"]} for o in ops if not qn or qn in o["title"].lower()][:20]
    cells = []
    if qn:
        for col in ws.df.columns:
            for rid, v in zip(ws.df.index.tolist(), ws.df[col].astype(str).tolist()):
                if qn in v.lower():
                    cells.append({"rid": int(rid), "column": col, "value": v[:80]})
                    if len(cells) >= 20:
                        break
            if len(cells) >= 20:
                break
    return {"pages": pages[:10], "columns": columns[:20], "issues": issues[:20], "rules": rules[:20], "history": history, "cells": cells}
