from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.schemas import DetectionConfig, Evidence, IssueGroup
from app.profiling.numbers import parse_number


def _k(config: DetectionConfig) -> tuple[float, float]:
    if config.outlier_sensitivity == "strict":
        return 1.5, 3.0
    if config.outlier_sensitivity == "relaxed":
        return 3.0, 4.5
    return 1.5, 3.5


def detect_outliers(df: pd.DataFrame, metas: list[dict], config: DetectionConfig) -> list[IssueGroup]:
    k, zthr = _k(config)
    groups: list[IssueGroup] = []
    meta_by = {m["name"]: m for m in metas}
    for col in df.columns:
        m = meta_by.get(col, {})
        et = m.get("effective_type")
        if et not in {"integer", "decimal"} or m.get("unique_auto") or m.get("is_unique_declared"):
            continue
        pairs = []
        for rid, v in zip(df.index.tolist(), df[col].astype(str).tolist()):
            n = parse_number(v)
            if n is not None:
                pairs.append((int(rid), n, v))
        if len(pairs) < config.outlier_min_values:
            continue
        arr = np.array([p[1] for p in pairs], dtype=float)
        if (arr == arr[0]).mean() > 0.95:
            continue
        q1, q3 = np.percentile(arr, 25), np.percentile(arr, 75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        work = arr
        log_note = False
        mean = arr.mean()
        std = arr.std() or 1
        skew = float(((arr - mean) ** 3).mean() / (std**3))
        if skew > 2 and (arr > 0).all():
            work = np.log1p(arr)
            q1, q3 = np.percentile(work, 25), np.percentile(work, 75)
            iqr = q3 - q1
            log_note = True
        low, high = q1 - k * iqr, q3 + k * iqr
        med = np.median(work)
        mad = np.median(np.abs(work - med))
        flagged = []
        for i, (rid, n, raw) in enumerate(pairs):
            x = work[i]
            if not (x < low or x > high):
                continue
            if mad == 0:
                continue
            rz = abs(0.6745 * (x - med) / mad)
            if rz > zthr:
                flagged.append((rid, n, raw))
        if not flagged:
            continue
        extra = " (checked on a log scale)" if log_note else ""
        n0, raw0 = flagged[0][1], flagged[0][2]
        reason = (
            f"{col} = {raw0} is far above the usual range (most values are between "
            f"{arr.min():.0f} and {np.percentile(arr, 75):.0f}; Q3 = {np.percentile(arr, 75):.0f}, "
            f"upper fence = {high:.0f}){extra}. Suspicious, not necessarily wrong."
        )
        groups.append(
            IssueGroup(
                key=f"outlier:iqr:{col}",
                type="outlier",
                subtype="iqr",
                column=col,
                columns=[col],
                severity="info",
                rids=[r for r, _, _ in flagged],
                cells=len(flagged),
                reason=reason,
                evidence=[Evidence(rid=r, column=col, value=raw, note="outlier") for r, _, raw in flagged[:5]],
                suggested_next_step="Review the value. We will not delete it unless you choose to.",
                stats={"q1": float(q1), "q3": float(q3), "iqr": float(iqr), "k": k},
                rid_count=len(flagged),
            )
        )
    return groups
