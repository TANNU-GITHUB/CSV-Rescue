from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from app.config import settings
from app.core.ids import new_id
from app.core.ingest import parse_csv_bytes, save_original
from app.core.locks import session_lock
from app.core.ops import apply_patch, invert_patch, read_patch, state_hash, undo_patch, write_patch
from app.core.schemas import DetectionConfig, SessionMeta
from app.core.working_set import CACHE, WorkingSet
from app.db import get_db
from app.errors import AppError
from app.profiling.profiler import profile_dataframe


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def session_dir(sid: str) -> Path:
    p = settings.DATA_DIR / "sessions" / sid
    p.mkdir(parents=True, exist_ok=True)
    return p


def purge_expired() -> None:
    db = get_db()
    now = _iso(_now())
    rows = db.execute("SELECT id FROM sessions WHERE expires_at < ?", (now,)).fetchall()
    for r in rows:
        delete_session(r["id"])


def create_session_from_bytes(
    raw: bytes, filename: str, delimiter: str | None = None, encoding: str | None = None, has_header: bool = True
) -> str:
    if len(raw) > settings.max_upload_bytes:
        raise AppError("FILE_TOO_LARGE", f"That file is {len(raw)} bytes.", f"The limit is {settings.MAX_UPLOAD_MB} MB.")
    ext = Path(filename).suffix.lower()
    if ext not in {".csv", ".tsv", ".txt", ""}:
        raise AppError("NOT_TEXT", "That file doesn't look like a CSV.", "Export it as CSV and try again.")
    df, report = parse_csv_bytes(raw, filename, delimiter, encoding, has_header)
    sid = new_id()
    folder = session_dir(sid)
    save_original(folder, raw, df, report)
    config = DetectionConfig()
    now = _now()
    db = get_db()
    db.execute(
        """INSERT INTO sessions (id, filename, created_at, updated_at, expires_at, stage, head_seq, settings_json, parse_report_json, n_rows_original, n_cols)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            sid,
            filename,
            _iso(now),
            _iso(now),
            _iso(now + timedelta(hours=settings.SESSION_TTL_HOURS)),
            "profiled",
            0,
            config.model_dump_json(),
            json.dumps(report),
            len(df),
            len(df.columns),
        ),
    )
    db.commit()
    ws = WorkingSet(session_id=sid, df=df.copy(), original=df.copy(), config=config, head_seq=0)
    CACHE.put(ws)
    return sid


def load_row(sid: str) -> dict:
    db = get_db()
    row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if not row:
        raise AppError("SESSION_NOT_FOUND", "We could not find that dataset.", "Upload it again.", status=404)
    data = dict(row)
    if data["expires_at"] < _iso(_now()):
        raise AppError("SESSION_EXPIRED", "That dataset expired after 24 hours.", "Upload it again to continue.", status=410)
    return data


def touch(sid: str) -> None:
    db = get_db()
    now = _now()
    db.execute(
        "UPDATE sessions SET updated_at=?, expires_at=? WHERE id=?",
        (_iso(now), _iso(now + timedelta(hours=settings.SESSION_TTL_HOURS)), sid),
    )
    db.commit()


def get_working_set(sid: str) -> WorkingSet:
    cached = CACHE.get(sid)
    if cached:
        return cached
    row = load_row(sid)
    folder = session_dir(sid)
    original = pd.read_pickle(folder / "original.pkl")
    db = get_db()
    ops = db.execute(
        "SELECT seq, patch_path, state_hash_after, status FROM operations WHERE session_id=? AND status='applied' ORDER BY seq",
        (sid,),
    ).fetchall()
    df = original.copy()
    last_hash = None
    for op in ops:
        patch = read_patch(Path(op["patch_path"]))
        df = apply_patch(df, patch, check=False)
        last_hash = op["state_hash_after"]
    if last_hash and state_hash(df) != last_hash:
        raise AppError("STATE_CORRUPT", "Saved history does not match the data.", "Reset to the original file.")
    config = DetectionConfig.model_validate_json(row["settings_json"])
    ws = WorkingSet(
        session_id=sid, df=df, original=original, config=config, head_seq=row["head_seq"]
    )
    CACHE.put(ws)
    return ws


def meta_from_row(row: dict, n_rows: int | None = None) -> SessionMeta:
    return SessionMeta(
        id=row["id"],
        filename=row["filename"],
        stage=row["stage"],
        head_seq=row["head_seq"],
        verified_seq=row["verified_seq"],
        verified_at=row["verified_at"],
        n_rows=n_rows if n_rows is not None else row["n_rows_original"],
        n_rows_original=row["n_rows_original"],
        n_cols=row["n_cols"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def update_settings(sid: str, config: DetectionConfig) -> None:
    db = get_db()
    db.execute("UPDATE sessions SET settings_json=?, updated_at=? WHERE id=?", (config.model_dump_json(), _iso(_now()), sid))
    db.commit()
    ws = CACHE.get(sid)
    if ws:
        ws.config = config
        ws.cache.clear()


def set_stage(sid: str, stage: str) -> None:
    db = get_db()
    db.execute("UPDATE sessions SET stage=?, updated_at=? WHERE id=?", (stage, _iso(_now()), sid))
    db.commit()


def apply_operation(
    sid: str,
    kind: str,
    title: str,
    params: dict,
    patch: dict,
    proposal_id: str | None = None,
    batch_id: str | None = None,
) -> dict:
    with session_lock(sid):
        ws = get_working_set(sid)
        before_hash = state_hash(ws.df)
        try:
            new_df = apply_patch(ws.df, patch, check=True)
        except AppError:
            raise
        op_id = new_id(8)
        seq = ws.head_seq + 1
        folder = session_dir(sid)
        patch_path = folder / "ops" / f"{op_id}.json.gz"
        patch.setdefault("meta", {})["action"] = kind
        patch["meta"]["params"] = params
        write_patch(patch_path, patch)
        after_hash = state_hash(new_df)
        cells = len(patch.get("cells") or [])
        deleted = len(patch.get("deleted_rows") or [])
        db = get_db()
        try:
            db.execute(
                """INSERT INTO operations (id, session_id, seq, batch_id, kind, title, params_json, status, proposal_id, created_at, affected_cells, affected_rows, rows_deleted, patch_path, state_hash_after)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    op_id,
                    sid,
                    seq,
                    batch_id,
                    kind,
                    title,
                    json.dumps(params),
                    "applied",
                    proposal_id,
                    _iso(_now()),
                    cells,
                    len({c["rid"] for c in patch.get("cells") or []}) + deleted,
                    deleted,
                    str(patch_path),
                    after_hash,
                ),
            )
            db.execute(
                "UPDATE operations SET status='discarded' WHERE session_id=? AND status='undone'",
                (sid,),
            )
            db.execute(
                "UPDATE sessions SET head_seq=?, stage=?, updated_at=?, verified_seq=CASE WHEN verified_seq IS NOT NULL AND verified_seq!=? THEN verified_seq END WHERE id=?",
                (seq, "reviewing", _iso(_now()), seq, sid),
            )
            # if previously verified, mark stale by leaving verified_seq behind
            db.commit()
        except Exception:
            db.rollback()
            raise
        ws.df = new_df
        ws.head_seq = seq
        ws.cache.clear()
        touch(sid)
        return {
            "id": op_id,
            "seq": seq,
            "kind": kind,
            "title": title,
            "status": "applied",
            "affected_cells": cells,
            "rows_deleted": deleted,
            "state_hash_after": after_hash,
            "before_hash": before_hash,
        }


def undo_latest(sid: str) -> dict:
    with session_lock(sid):
        ws = get_working_set(sid)
        db = get_db()
        op = db.execute(
            "SELECT * FROM operations WHERE session_id=? AND status='applied' ORDER BY seq DESC LIMIT 1",
            (sid,),
        ).fetchone()
        if not op:
            raise AppError("NOTHING_TO_UNDO", "There is nothing to undo.", "Apply a change first.")
        patch = read_patch(Path(op["patch_path"]))
        ws.df = undo_patch(ws.df, patch)
        db.execute(
            "UPDATE operations SET status='undone', undone_at=? WHERE id=?",
            (_iso(_now()), op["id"]),
        )
        prev = db.execute(
            "SELECT seq FROM operations WHERE session_id=? AND status='applied' ORDER BY seq DESC LIMIT 1",
            (sid,),
        ).fetchone()
        new_seq = prev["seq"] if prev else 0
        db.execute("UPDATE sessions SET head_seq=?, stage=?, updated_at=? WHERE id=?", (new_seq, "reviewing", _iso(_now()), sid))
        db.commit()
        ws.head_seq = new_seq
        ws.cache.clear()
        return {"id": op["id"], "title": op["title"], "status": "undone"}


def redo_latest(sid: str) -> dict:
    with session_lock(sid):
        ws = get_working_set(sid)
        db = get_db()
        op = db.execute(
            "SELECT * FROM operations WHERE session_id=? AND status='undone' ORDER BY seq ASC LIMIT 1",
            (sid,),
        ).fetchone()
        if not op:
            raise AppError("NOTHING_TO_REDO", "There is nothing to redo.", "")
        patch = read_patch(Path(op["patch_path"]))
        ws.df = apply_patch(ws.df, patch, check=False)
        db.execute("UPDATE operations SET status='applied', undone_at=NULL WHERE id=?", (op["id"],))
        db.execute("UPDATE sessions SET head_seq=?, updated_at=? WHERE id=?", (op["seq"], _iso(_now()), sid))
        db.commit()
        ws.head_seq = op["seq"]
        ws.cache.clear()
        return {"id": op["id"], "title": op["title"], "status": "applied"}


def delete_session(sid: str) -> None:
    import shutil

    db = get_db()
    db.execute("DELETE FROM operations WHERE session_id=?", (sid,))
    db.execute("DELETE FROM rules WHERE session_id=?", (sid,))
    db.execute("DELETE FROM decisions WHERE session_id=?", (sid,))
    db.execute("DELETE FROM dismissals WHERE session_id=?", (sid,))
    db.execute("DELETE FROM sessions WHERE id=?", (sid,))
    db.commit()
    CACHE.drop(sid)
    folder = settings.DATA_DIR / "sessions" / sid
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


def list_summaries(ids: list[str]) -> list[dict]:
    db = get_db()
    out = []
    for sid in ids:
        row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            continue
        if row["expires_at"] < _iso(_now()):
            continue
        out.append(
            {
                "id": row["id"],
                "filename": row["filename"],
                "rows": row["n_rows_original"],
                "columns": row["n_cols"],
                "updated_at": row["updated_at"],
                "stage": row["stage"],
            }
        )
    return out
