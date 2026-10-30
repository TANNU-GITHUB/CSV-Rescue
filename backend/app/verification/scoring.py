from __future__ import annotations

from app.core.schemas import IssueGroup


def quality_scores(n_rows: int, n_cols: int, groups: list[IssueGroup]) -> dict:
    open_groups = [g for g in groups if g.status == "open"]
    dirty_rows: set[int] = set()
    dirty_cells: set[tuple[int, str]] = set()
    findings = 0
    for g in open_groups:
        for rid in g.rids:
            dirty_rows.add(rid)
            findings += 1
            cols = g.columns or ([g.column] if g.column else [])
            if g.type in {"duplicate_row", "duplicate_id"} or (g.column is None and len(cols) > 1):
                for c in cols:
                    dirty_cells.add((rid, c))
            else:
                for c in cols or [g.column]:
                    if c:
                        dirty_cells.add((rid, c))
    n_rows = max(n_rows, 1)
    row_q = 100.0 * (n_rows - len(dirty_rows)) / n_rows
    if findings and round(row_q, 1) == 100.0:
        row_q = 99.9
    cell_q = 100.0 * (1 - len(dirty_cells) / max(n_rows * max(n_cols, 1), 1))
    return {
        "quality_score": round(row_q, 1),
        "cell_quality": round(cell_q, 1),
        "open_findings": findings,
        "dirty_rows": len(dirty_rows),
    }
