from __future__ import annotations

from fastapi import APIRouter

from app.core.ops import patch_from_changes
from app.core.pipeline import detect_current, profile_for
from app.core.schemas import Change
from app.core.session_store import apply_operation, get_working_set, load_row
from app.detection.engine import issue_masks
from app.errors import AppError

router = APIRouter()


@router.get("/sessions/{sid}/rows")
def rows(sid: str, view: str = "current", offset: int = 0, limit: int = 100, q: str = "", only_issues: bool = False, sort: str | None = None, dir: str = "asc"):
    limit = min(limit, 500)
    ws = get_working_set(sid)
    df = ws.original if view == "original" else ws.df
    groups, _ = detect_current(sid)
    mask = issue_masks(groups, list(df.columns))
    index = list(df.index)
    if q:
        ql = q.lower()
        index = [i for i in index if any(ql in str(df.at[i, c]).lower() for c in df.columns)]
    if only_issues:
        dirty = {rid for rid, _ in mask}
        index = [i for i in index if i in dirty]
    if sort and sort in df.columns:
        index = sorted(index, key=lambda i: str(df.at[i, sort]), reverse=dir == "desc")
    total = len(index)
    slice_ids = index[offset : offset + limit]
    out_rows = []
    for rid in slice_ids:
        cells = {}
        issues = {}
        for c in df.columns:
            cells[c] = str(df.at[rid, c])
            keys = mask.get((rid, c))
            if keys:
                issues[c] = keys
        out_rows.append({"rid": int(rid), "row_number": int(rid) + 1, "cells": cells, "issue_keys": issues})
    return {"total": total, "offset": offset, "limit": limit, "columns": list(df.columns), "rows": out_rows}


@router.get("/sessions/{sid}/profile")
def profile(sid: str, view: str = "current"):
    row = load_row(sid)
    data = profile_for(sid, view)
    data["parse_report"] = __import__("json").loads(row["parse_report_json"])
    groups, _ = detect_current(sid)
    counts: dict[str, int] = {}
    for g in groups:
        if g.status == "open" and g.column:
            counts[g.column] = counts.get(g.column, 0) + 1
    for card in data["column_cards"]:
        card["open_issues"] = counts.get(card["name"], 0)
    return data


@router.put("/sessions/{sid}/columns/{name}/type")
def override_type(sid: str, name: str, body: dict):
    ws = get_working_set(sid)
    if name not in ws.df.columns:
        raise AppError("COLUMN_NOT_FOUND", f"No column named {name}.", "")
    cfg = ws.config
    cfg.type_overrides[name] = body.get("type")
    from app.core.session_store import update_settings

    update_settings(sid, cfg)
    ws.cache.clear()
    return {"ok": True}


@router.post("/sessions/{sid}/cells")
def edit_cell(sid: str, body: dict):
    ws = get_working_set(sid)
    rid, col, value = int(body["rid"]), body["column"], str(body.get("value", ""))
    if col not in ws.df.columns or rid not in ws.df.index:
        raise AppError("COLUMN_NOT_FOUND", "That cell does not exist.", "")
    old = str(ws.df.at[rid, col])
    ch = Change(id=f"{rid}:{col}", kind="cell_update", rid=rid, column=col, before=old, after=value, reason="Manual edit", confidence=1, selected=True)
    patch = patch_from_changes([ch], ws.df)
    op = apply_operation(sid, "manual_edit", f"Edit {col} row {rid+1}", {"rid": rid, "column": col}, patch)
    return {"op": op}
