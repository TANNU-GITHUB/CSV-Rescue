from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.schemas import DetectionConfig, IssueGroup
from app.detection.duplicates import detect_duplicate_rows
from app.detection.formats import detect_formats
from app.detection.identifiers import detect_duplicate_ids
from app.detection.missing import detect_missing
from app.detection.numeric import detect_invalid_numeric
from app.detection.outliers import detect_outliers
from app.detection.rule_findings import groups_from_rule_results
from app.detection.text import detect_text
from app.profiling.profiler import profile_dataframe


def _sev_rank(s: str) -> int:
    return {"error": 0, "warning": 1, "info": 2}.get(s, 9)


def run_detection(
    df: pd.DataFrame,
    config: DetectionConfig,
    rules_results: list[dict] | None = None,
    dismissals: dict[str, set[int]] | None = None,
) -> list[IssueGroup]:
    profile = profile_dataframe(df, config)
    metas = profile["column_meta"]
    groups: list[IssueGroup] = []
    groups += detect_missing(df, config)
    groups += detect_duplicate_rows(df, config)
    groups += detect_text(df, metas, config)
    groups += detect_formats(df, metas, config)
    groups += detect_invalid_numeric(df, metas, config)
    groups += detect_outliers(df, metas, config)
    groups += detect_duplicate_ids(df, metas, config)
    if rules_results:
        groups += groups_from_rule_results(rules_results, df)
    dismissals = dismissals or {}
    for g in groups:
        dismissed = dismissals.get(g.key, set())
        open_rids = [r for r in g.rids if r not in dismissed]
        if not open_rids and g.rids:
            g.status = "dismissed"
        g.rids = open_rids if g.status != "dismissed" else g.rids
        g.rid_count = len(g.rids)
        g.cells = max(g.cells, len(g.rids))
    groups.sort(key=lambda g: (_sev_rank(g.severity), -g.cells, g.key))
    return groups


def issue_masks(groups: list[IssueGroup], columns: list[str]) -> dict[tuple[int, str], list[str]]:
    mask: dict[tuple[int, str], list[str]] = {}
    for g in groups:
        if g.status != "open":
            continue
        cols = g.columns or ([g.column] if g.column else columns)
        for rid in g.rids:
            for c in cols:
                mask.setdefault((rid, c), []).append(g.key)
    return mask
