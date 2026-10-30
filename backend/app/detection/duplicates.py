from __future__ import annotations

import pandas as pd

from app.core.schemas import DetectionConfig, Evidence, IssueGroup


def detect_duplicate_rows(df: pd.DataFrame, config: DetectionConfig) -> list[IssueGroup]:
    cols = [c for c in df.columns if c not in config.duplicate_ignore_columns]
    if df.empty or not cols:
        return []
    mask = df.duplicated(subset=cols, keep="first")
    rids = [int(i) for i in df.index[mask].tolist()]
    if not rids:
        return []
    firsts = []
    for rid in rids[:5]:
        row = df.loc[rid]
        # find original
        match = (df.loc[~mask, cols] == row[cols]).all(axis=1)
        first = int(df.index[~mask][match][0]) if match.any() else 0
        firsts.append(first)
    ev = [
        Evidence(rid=r, column="*", value=f"identical to row {firsts[i]+1}", note=f"first_rid={firsts[i]}")
        for i, r in enumerate(rids[:5])
    ]
    first_rid = firsts[0] if firsts else 0
    reason = f"Row {rids[0] + 1} is identical to row {first_rid + 1} in every column."
    return [
        IssueGroup(
            key="duplicate_row:exact:*",
            type="duplicate_row",
            subtype="exact",
            column=None,
            columns=list(cols),
            severity="error",
            rids=rids,
            cells=len(rids) * len(cols),
            reason=reason,
            evidence=ev,
            suggested_next_step="Keep the first copy and remove the extras (this deletes rows — you can undo)",
            rid_count=len(rids),
        )
    ]
