from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.core.ops import read_patch
from app.core.session_store import get_working_set, load_row, meta_from_row, redo_latest, undo_latest
from app.db import get_db

router = APIRouter()


@router.get("/sessions/{sid}/history")
def history(sid: str):
    db = get_db()
    ops = [dict(r) for r in db.execute("SELECT * FROM operations WHERE session_id=? ORDER BY seq DESC", (sid,)).fetchall()]
    counts = {
        "applied": sum(1 for o in ops if o["status"] == "applied"),
        "undone": sum(1 for o in ops if o["status"] == "undone"),
        "rejected": db.execute("SELECT COUNT(*) n FROM decisions WHERE session_id=? AND status='rejected'", (sid,)).fetchone()["n"],
        "skipped": db.execute("SELECT COUNT(*) n FROM decisions WHERE session_id=? AND status='skipped'", (sid,)).fetchone()["n"],
    }
    return {"items": ops, "counts": counts}


@router.get("/sessions/{sid}/history/{op_id}")
def history_one(sid: str, op_id: str, offset: int = 0, limit: int = 50):
    db = get_db()
    op = db.execute("SELECT * FROM operations WHERE id=? AND session_id=?", (op_id, sid)).fetchone()
    if not op:
        return {"op": None, "changes": []}
    patch = read_patch(Path(op["patch_path"]))
    cells = patch.get("cells") or []
    return {"op": dict(op), "changes": cells[offset : offset + limit], "total": len(cells), "deleted": patch.get("deleted_rows") or []}


@router.post("/sessions/{sid}/undo")
def undo(sid: str):
    op = undo_latest(sid)
    row = load_row(sid)
    ws = get_working_set(sid)
    return {"op": op, "session": meta_from_row(row, len(ws.df)).model_dump()}


@router.post("/sessions/{sid}/redo")
def redo(sid: str):
    op = redo_latest(sid)
    row = load_row(sid)
    ws = get_working_set(sid)
    return {"op": op, "session": meta_from_row(row, len(ws.df)).model_dump()}
