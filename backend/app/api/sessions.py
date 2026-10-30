from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.core.ingest import parse_csv_bytes, save_original
from app.core.pipeline import detect_current, profile_for
from app.core.schemas import DetectionConfig
from app.core.session_store import (
    create_session_from_bytes,
    delete_session,
    get_working_set,
    list_summaries,
    load_row,
    meta_from_row,
    session_dir,
    touch,
    update_settings,
)
from app.db import get_db
from app.errors import AppError

router = APIRouter()


def _created(sid: str) -> dict:
    row = load_row(sid)
    ws = get_working_set(sid)
    groups, _ = detect_current(sid)
    prof = profile_for(sid)
    return {
        "session_id": sid,
        "filename": row["filename"],
        "parse_report": json.loads(row["parse_report_json"]),
        "dataset": {"rows": len(ws.df), "columns": list(ws.df.columns)},
        "profile_summary": {"rows": prof["rows"], "columns": prof["columns"], "missing_cells": prof["missing_cells"], "duplicate_rows": prof["duplicate_rows"]},
        "issue_summary": {"groups": len(groups), "open": sum(1 for g in groups if g.status == "open")},
        "session": meta_from_row(row, len(ws.df)).model_dump(),
    }


@router.post("/sessions")
async def upload(
    file: UploadFile = File(...),
    delimiter: str | None = Form(None),
    encoding: str | None = Form(None),
    has_header: bool = Form(True),
):
    raw = await file.read()
    sid = create_session_from_bytes(raw, file.filename or "upload.csv", delimiter, encoding, has_header)
    return _created(sid)


@router.post("/sessions/sample")
def sample(body: dict):
    name = body.get("sample", "students")
    fname = "students_messy.csv" if name != "sales" else "sales_messy.csv"
    path = Path(__file__).resolve().parents[1] / "samples" / fname
    if not path.exists():
        from app.samples.generate_samples import main as gen

        gen()
    raw = path.read_bytes()
    sid = create_session_from_bytes(raw, fname)
    return _created(sid)


@router.get("/sessions/summary")
def summary(ids: str = ""):
    return {"items": list_summaries([i for i in ids.split(",") if i])}


@router.get("/sessions/{sid}")
def get_session(sid: str):
    row = load_row(sid)
    ws = get_working_set(sid)
    return meta_from_row(row, len(ws.df)).model_dump()


@router.get("/sessions/{sid}/status")
def status(sid: str):
    load_row(sid)
    return {"status": "ready"}


@router.post("/sessions/{sid}/reparse")
def reparse(sid: str, body: dict):
    row = load_row(sid)
    folder = session_dir(sid)
    raw = (folder / "original.csv").read_bytes()
    df, report = parse_csv_bytes(
        raw,
        row["filename"],
        body.get("delimiter"),
        body.get("encoding"),
        body.get("has_header", True),
    )
    save_original(folder, raw, df, report)
    db = get_db()
    db.execute("DELETE FROM operations WHERE session_id=?", (sid,))
    db.execute(
        "UPDATE sessions SET parse_report_json=?, head_seq=0, n_rows_original=?, n_cols=?, stage='profiled' WHERE id=?",
        (json.dumps(report), len(df), len(df.columns), sid),
    )
    db.commit()
    from app.core.working_set import CACHE

    CACHE.drop(sid)
    return _created(sid)


@router.put("/sessions/{sid}/settings")
def settings_put(sid: str, body: dict):
    ws = get_working_set(sid)
    cfg = DetectionConfig.model_validate({**ws.config.model_dump(), **body})
    update_settings(sid, cfg)
    ws.cache.clear()
    return {"ok": True, "settings": cfg.model_dump()}


@router.delete("/sessions/{sid}", status_code=204)
def remove(sid: str):
    delete_session(sid)
    return None
