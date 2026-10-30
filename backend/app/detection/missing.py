from __future__ import annotations

import pandas as pd

from app.core.schemas import DetectionConfig, Evidence, IssueGroup


def detect_missing(df: pd.DataFrame, config: DetectionConfig) -> list[IssueGroup]:
    tokens = {t.lower() for t in config.missing_tokens}
    groups: list[IssueGroup] = []
    for col in df.columns:
        blank_rids: list[int] = []
        disguised: list[tuple[int, str]] = []
        for rid, v in zip(df.index.tolist(), df[col].astype(str).tolist()):
            s = v
            if s.strip() == "":
                blank_rids.append(int(rid))
            elif s.strip().lower() in tokens:
                disguised.append((int(rid), s))
        if blank_rids:
            ev = [Evidence(rid=r, column=col, value="", note="blank") for r in blank_rids[:5]]
            groups.append(
                IssueGroup(
                    key=f"missing_value:blank:{col}",
                    type="missing_value",
                    subtype="blank",
                    column=col,
                    columns=[col],
                    severity="warning",
                    rids=blank_rids,
                    cells=len(blank_rids),
                    reason="Value is blank",
                    evidence=ev,
                    suggested_next_step="Fill with the median/mode or leave the blanks — you choose",
                    rid_count=len(blank_rids),
                )
            )
        if disguised:
            ev = [Evidence(rid=r, column=col, value=val, note="placeholder") for r, val in disguised[:5]]
            sample = disguised[0][1]
            groups.append(
                IssueGroup(
                    key=f"missing_value:disguised:{col}",
                    type="missing_value",
                    subtype="disguised",
                    column=col,
                    columns=[col],
                    severity="warning",
                    rids=[r for r, _ in disguised],
                    cells=len(disguised),
                    reason=f"'{sample.strip()}' is a placeholder for a missing value.",
                    evidence=ev,
                    suggested_next_step="Convert placeholders to blank, then decide how to fill",
                    rid_count=len(disguised),
                )
            )
    return groups
