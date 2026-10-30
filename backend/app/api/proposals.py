from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import unquote

from fastapi import APIRouter

from app.cleaning.registry import BY_ID
from app.core.ops import patch_from_changes
from app.core.pipeline import detect_current, proposals_for
from app.core.session_store import apply_operation, get_working_set
from app.db import get_db
from app.errors import AppError

router = APIRouter()


def _get(sid: str, key: str):
    key = unquote(key)
    props = proposals_for(sid)
    p = next((x for x in props if x.key == key), None)
    if not p:
        raise AppError("VALIDATION_ERROR", "That suggestion is no longer available.", "Refresh the studio.")
    return p


@router.get("/sessions/{sid}/proposals")
def list_props(sid: str, status: str | None = None, risk: str | None = None, column: str | None = None):
    items = proposals_for(sid)
    out = []
    for p in items:
        if status and p.status != status:
            continue
        if risk and p.risk != risk:
            continue
        if column and p.column != column:
            continue
        d = p.model_dump()
        d.pop("changes", None)
        out.append(d)
    return {"items": out}


@router.get("/sessions/{sid}/proposals/{key}")
def detail(sid: str, key: str):
    p = _get(sid, key)
    d = p.model_dump()
    d["changes_total"] = len(p.changes)
    d.pop("changes", None)
    return d


@router.get("/sessions/{sid}/proposals/{key}/changes")
def changes(sid: str, key: str, offset: int = 0, limit: int = 200, only_uncertain: bool = False):
    p = _get(sid, key)
    ch = p.changes
    if only_uncertain:
        ch = [c for c in ch if c.confidence < 0.9 or not c.selected]
    ws = get_working_set(sid)
    items = []
    for change in ch[offset : offset + min(limit, 2000)]:
        item = change.model_dump()
        if change.kind == "row_delete":
            item["row"] = {column: str(ws.df.at[change.rid, column]) for column in ws.df.columns}
        items.append(item)
    return {"total": len(ch), "items": items}


@router.patch("/sessions/{sid}/proposals/{key}")
def patch_params(sid: str, key: str, body: dict):
    key = unquote(key)
    p = _get(sid, key)
    action = BY_ID[p.action]
    groups, _ = detect_current(sid)
    issue = next((g for g in groups if g.key in p.issue_keys), None)
    params = {**p.params, **(body.get("params") or body)}
    if issue is None:
        raise AppError("VALIDATION_ERROR", "That issue is no longer available.", "Refresh the studio.")
    changes = action.build_changes(get_working_set(sid).df, params, issue=issue)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO proposal_settings (session_id, proposal_key, params_json) VALUES (?,?,?)",
        (sid, key, json.dumps(params)),
    )
    db.commit()
    get_working_set(sid).cache.clear()
    p.params = params
    p.changes = changes
    p.cells_affected = sum(1 for c in changes if c.kind == "cell_update")
    p.rows_deleted = sum(1 for c in changes if c.kind == "row_delete")
    d = p.model_dump()
    d.pop("changes", None)
    d["changes_total"] = len(changes)
    return d


@router.patch("/sessions/{sid}/proposals/{key}/changes/{change_id}")
def override_change(sid: str, key: str, change_id: str, body: dict):
    return {"ok": True, "change_id": change_id, "override": body.get("override")}


@router.post("/sessions/{sid}/proposals/{key}/apply")
def apply(sid: str, key: str, body: dict | None = None):
    body = body or {}
    p = _get(sid, key)
    ws = get_working_set(sid)
    if p.based_on_seq != ws.head_seq:
        raise AppError("PREVIEW_STALE", "Your data changed since this preview was made.", "Review the refreshed preview and try again.", status=409)
    if p.risk == "destructive" and not body.get("confirm_destructive"):
        raise AppError("VALIDATION_ERROR", "Tick the confirmation box to remove rows.", "")
    selected = body.get("change_ids")
    overrides = body.get("overrides") or {}
    changes = []
    for c in p.changes:
        if selected is not None and c.id not in selected:
            continue
        if selected is None and not c.selected:
            continue
        if c.id in overrides:
            c.override = str(overrides[c.id])
        changes.append(c)
    patch = patch_from_changes(changes, ws.df)
    op = apply_operation(sid, p.action, p.title, p.params, patch, proposal_id=p.key)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO decisions (session_id, proposal_key, status, reason, updated_at) VALUES (?,?,?,?,?)",
        (sid, p.key, "accepted", None, datetime.now(UTC).isoformat()),
    )
    db.commit()
    return {"op": op}


@router.post("/sessions/{sid}/proposals/{key}/reject")
def reject(sid: str, key: str, body: dict | None = None):
    key = unquote(key)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO decisions (session_id, proposal_key, status, reason, updated_at) VALUES (?,?,?,?,?)",
        (sid, key, "rejected", (body or {}).get("reason"), datetime.now(UTC).isoformat()),
    )
    db.commit()
    return {"ok": True}


@router.post("/sessions/{sid}/proposals/{key}/skip")
def skip(sid: str, key: str):
    key = unquote(key)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO decisions (session_id, proposal_key, status, reason, updated_at) VALUES (?,?,?,?,?)",
        (sid, key, "skipped", None, datetime.now(UTC).isoformat()),
    )
    db.commit()
    return {"ok": True}


@router.post("/sessions/{sid}/proposals/{key}/reopen")
def reopen(sid: str, key: str):
    key = unquote(key)
    db = get_db()
    db.execute("DELETE FROM decisions WHERE session_id=? AND proposal_key=?", (sid, key))
    db.commit()
    return {"ok": True}


@router.post("/sessions/{sid}/proposals/apply-safe")
def apply_safe(sid: str):
    from app.core.ids import new_id

    batch = new_id(6)
    ops = []
    # Rebuild after each apply so later previews match the live DataFrame.
    seen: set[str] = set()
    while True:
        props = [p for p in proposals_for(sid) if p.status == "pending" and p.risk == "safe" and p.key not in seen]
        if not props:
            break
        p = props[0]
        seen.add(p.key)
        changes = [c for c in p.changes if c.selected]
        if not changes:
            continue
        patch = patch_from_changes(changes, get_working_set(sid).df)
        try:
            op = apply_operation(sid, p.action, p.title, p.params, patch, proposal_id=p.key, batch_id=batch)
        except AppError as e:
            if e.code == "STATE_MISMATCH":
                continue
            raise
        ops.append(op)
        db = get_db()
        db.execute(
            "INSERT OR REPLACE INTO decisions (session_id, proposal_key, status, reason, updated_at) VALUES (?,?,?,?,?)",
            (sid, p.key, "accepted", "apply-safe", datetime.now(UTC).isoformat()),
        )
        db.commit()
        get_working_set(sid).cache.clear()
    return {"ops": ops, "batch_id": batch}
