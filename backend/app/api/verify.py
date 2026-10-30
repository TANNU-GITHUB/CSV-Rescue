from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.pipeline import detect_current, detect_original
from app.core.session_store import get_working_set, load_row, set_stage
from app.db import get_db
from app.verification.verify import verify as run_verify

router = APIRouter()
_LAST: dict[str, dict] = {}


def _actions(sid: str) -> dict:
    db = get_db()
    ops = db.execute("SELECT status, affected_cells, rows_deleted FROM operations WHERE session_id=?", (sid,)).fetchall()
    dec = db.execute("SELECT status FROM decisions WHERE session_id=?", (sid,)).fetchall()
    return {
        "applied": sum(1 for o in ops if o["status"] == "applied"),
        "undone": sum(1 for o in ops if o["status"] == "undone"),
        "rejected": sum(1 for d in dec if d["status"] == "rejected"),
        "skipped": sum(1 for d in dec if d["status"] == "skipped"),
        "cells_changed": sum(o["affected_cells"] or 0 for o in ops if o["status"] == "applied"),
        "rows_deleted": sum(o["rows_deleted"] or 0 for o in ops if o["status"] == "applied"),
    }


@router.post("/sessions/{sid}/verify")
def verify(sid: str):
    ws = get_working_set(sid)
    before_g, before_r = detect_original(sid)
    after_g, after_r = detect_current(sid)
    result = run_verify(before_g, after_g, len(ws.original), len(ws.df), len(ws.df.columns), before_r, after_r, _actions(sid), ws.head_seq)
    result["verified_at"] = datetime.now(timezone.utc).isoformat()
    db = get_db()
    db.execute(
        "UPDATE sessions SET verified_seq=?, verified_at=?, stage=? WHERE id=?",
        (ws.head_seq, result["verified_at"], "verified", sid),
    )
    db.commit()
    _LAST[sid] = result
    ( __import__("pathlib").Path )  # keep import light
    from app.core.session_store import session_dir

    (session_dir(sid) / "last_verification.json").write_text(json.dumps(result, default=str), encoding="utf-8")
    return result


@router.get("/sessions/{sid}/verification")
def latest(sid: str):
    row = load_row(sid)
    result = _LAST.get(sid)
    if not result:
        from pathlib import Path
        from app.core.session_store import session_dir

        p = session_dir(sid) / "last_verification.json"
        if p.exists():
            result = json.loads(p.read_text())
    stale = True
    if result and row["verified_seq"] == row["head_seq"]:
        stale = False
    if result and stale:
        result = {**result, "verdict": "stale"}
    return {"result": result, "stale": stale}
