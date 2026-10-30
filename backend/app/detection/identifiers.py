from __future__ import annotations

import re
from collections import defaultdict

import pandas as pd

from app.core.schemas import DetectionConfig, Evidence, IssueGroup


def detect_duplicate_ids(df: pd.DataFrame, metas: list[dict], config: DetectionConfig) -> list[IssueGroup]:
    groups: list[IssueGroup] = []
    unique_re = re.compile(config.unique_name_patterns, re.I)
    meta_by = {m["name"]: m for m in metas}
    for col in df.columns:
        m = meta_by.get(col, {})
        series = df[col].astype(str)
        nonblank = [v for v in series if v.strip()]
        if not nonblank:
            continue
        distinct = len({v.strip().casefold() for v in nonblank})
        ratio = distinct / len(nonblank)
        declared = col in config.unique_columns or m.get("is_unique_declared")
        name_match = bool(unique_re.search(col))
        auto = bool(name_match and (ratio >= config.unique_min_distinct_ratio or name_match))
        # Name-pattern ID columns are always uniqueness-checked; ratio only drives the auto badge.
        if not declared and not name_match:
            continue
        buckets: dict[str, list[int]] = defaultdict(list)
        for rid, v in zip(df.index.tolist(), series.tolist()):
            if not v.strip():
                continue
            buckets[v.strip().casefold()].append(int(rid))
        conflict_rids: list[int] = []
        ev: list[Evidence] = []
        for val, ids in buckets.items():
            if len(ids) > 1:
                conflict_rids.extend(ids)
                if len(ev) < 5:
                    ev.append(Evidence(rid=ids[0], column=col, value=val, note=f"rids={ids}"))
        if conflict_rids:
            groups.append(
                IssueGroup(
                    key=f"duplicate_id:repeat:{col}",
                    type="duplicate_id",
                    subtype="repeat",
                    column=col,
                    columns=[col],
                    severity="error",
                    rids=sorted(set(conflict_rids)),
                    cells=len(set(conflict_rids)),
                    reason=f"The same {col} appears on more than one row.",
                    evidence=ev,
                    suggested_next_step="Review conflicting rows side by side — never auto-resolved",
                    stats={"auto_detected": auto and not declared},
                    rid_count=len(set(conflict_rids)),
                )
            )
    return groups
