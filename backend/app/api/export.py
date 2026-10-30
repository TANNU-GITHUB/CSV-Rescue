from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app import __version__
from app.api.verify import latest, verify as run_verify
from app.core.session_store import get_working_set, load_row, set_stage
from app.reporting.exporter import attachment, df_to_csv_bytes, zip_bundle
from app.reporting.report import render_html

router = APIRouter()


def _verification(sid: str) -> dict:
    data = latest(sid)
    if not data.get("result") or data.get("stale"):
        return run_verify(sid)
    return data["result"]


@router.get("/sessions/{sid}/report")
def report(sid: str, format: str = "json"):
    row = load_row(sid)
    result = _verification(sid)
    if format == "html":
        html = render_html(row["filename"], result)
        return attachment(html.encode("utf-8"), Path(row["filename"]).stem + "_report.html", "text/html")
    payload = {"report_schema_version": 1, "filename": row["filename"], "version": __version__, **result}
    return payload


@router.get("/sessions/{sid}/export/csv")
def export_csv(sid: str, delimiter: str = ",", encoding: str = "utf-8", line_ending: str = "\n", escape_formulas: bool = False):
    ws = get_working_set(sid)
    row = load_row(sid)
    data = df_to_csv_bytes(ws.df, delimiter, encoding, line_ending.replace("\\n", "\n").replace("\\r\\n", "\r\n"), escape_formulas)
    set_stage(sid, "exported")
    return attachment(data, Path(row["filename"]).stem + "_cleaned.csv", "text/csv")


@router.get("/sessions/{sid}/export/history")
def export_history(sid: str, format: str = "json"):
    from app.api.history import history

    payload = history(sid)
    row = load_row(sid)
    if format == "csv":
        from app.db import get_db
        from app.core.ops import read_patch

        db = get_db()
        ops = db.execute("SELECT * FROM operations WHERE session_id=? ORDER BY seq", (sid,)).fetchall()
        lines = ["op_seq,op_kind,status,created_at,row_number,column,old_value,new_value"]
        for op in ops:
            patch = read_patch(Path(op["patch_path"]))
            for c in patch.get("cells") or []:
                lines.append(
                    ",".join(
                        str(x).replace(",", " ")
                        for x in [op["seq"], op["kind"], op["status"], op["created_at"], c["rid"] + 1, c["col"], c["old"], c["new"]]
                    )
                )
        return attachment("\n".join(lines).encode(), Path(row["filename"]).stem + "_history.csv", "text/csv")
    return attachment(json.dumps(payload, default=str).encode(), Path(row["filename"]).stem + "_history.json", "application/json")


@router.get("/sessions/{sid}/export/bundle")
def bundle(sid: str):
    row = load_row(sid)
    ws = get_working_set(sid)
    result = _verification(sid)
    stem = Path(row["filename"]).stem
    html = render_html(row["filename"], result)
    from app.api.history import history
    from app.core.pipeline import load_rules

    files = {
        f"{stem}_cleaned.csv": df_to_csv_bytes(ws.df),
        f"{stem}_report.html": html.encode(),
        f"{stem}_report.json": json.dumps({"report_schema_version": 1, **result}, default=str).encode(),
        f"{stem}_history.json": json.dumps(history(sid), default=str).encode(),
        f"{stem}_history.csv": b"op_seq,status\n",
        f"{stem}_rules.json": json.dumps([r.model_dump() for r in load_rules(sid)]).encode(),
        "README.txt": b"CSV Rescue export bundle. Open the HTML report in a browser.",
    }
    set_stage(sid, "exported")
    return zip_bundle(files, f"{stem}_csvrescue.zip")
