from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

from app.errors import AppError


def state_hash(df: pd.DataFrame) -> str:
    h = pd.util.hash_pandas_object(df.astype(str), index=True).sum()
    return hex(int(h) & ((1 << 64) - 1))


def write_patch(path: Path, patch: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(patch).encode("utf-8")))


def read_patch(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))


def apply_patch(df: pd.DataFrame, patch: dict, *, check: bool = True) -> pd.DataFrame:
    out = df.copy()
    for cell in patch.get("cells") or []:
        rid, col, old, new = cell["rid"], cell["col"], cell["old"], cell["new"]
        if rid not in out.index:
            if check:
                raise AppError("STATE_MISMATCH", "A cell changed since this preview.", "Refresh and try again.")
            continue
        current = str(out.at[rid, col])
        if check and current != old:
            raise AppError("STATE_MISMATCH", "A cell changed since this preview.", "Refresh and try again.")
        out.at[rid, col] = new
    deleted = patch.get("deleted_rows") or []
    if deleted:
        rids = [d["rid"] for d in deleted]
        out = out.drop(index=[r for r in rids if r in out.index], errors="ignore")
    return out


def invert_patch(patch: dict) -> dict:
    cells = [{"rid": c["rid"], "col": c["col"], "old": c["new"], "new": c["old"]} for c in patch.get("cells") or []]
    return {"cells": cells, "deleted_rows": patch.get("deleted_rows") or [], "restore": True, "meta": patch.get("meta")}


def undo_patch(df: pd.DataFrame, patch: dict) -> pd.DataFrame:
    out = df.copy()
    for cell in patch.get("cells") or []:
        rid, col, old = cell["rid"], cell["col"], cell["old"]
        if rid in out.index:
            out.at[rid, col] = old
    for d in patch.get("deleted_rows") or []:
        rid = d["rid"]
        values = d["values"]
        row = pd.DataFrame([values], index=[rid])
        out = pd.concat([out, row])
    out = out.sort_index()
    # restore column order if possible
    return out


def patch_from_changes(changes: list, df: pd.DataFrame) -> dict:
    cells = []
    deleted = []
    for ch in changes:
        if ch.kind == "cell_update":
            after = ch.override if ch.override is not None else ch.after
            cells.append({"rid": ch.rid, "col": ch.column, "old": ch.before, "new": after})
        else:
            values = {c: str(df.at[ch.rid, c]) for c in df.columns} if ch.rid in df.index else {}
            deleted.append({"rid": ch.rid, "values": values})
    return {"cells": cells, "deleted_rows": deleted, "meta": {}}
