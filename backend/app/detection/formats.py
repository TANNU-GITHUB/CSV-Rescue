from __future__ import annotations

from collections import Counter

import pandas as pd

from app.core.schemas import DetectionConfig, Evidence, IssueGroup
from app.profiling.dates import classify_date
from app.profiling.numbers import clean_numeric_token, parse_number

BOOL_FAMILIES = {
    "yes_no": {"yes", "no"},
    "y_n": {"y", "n"},
    "true_false": {"true", "false"},
    "one_zero": {"1", "0"},
}


def detect_formats(df: pd.DataFrame, metas: list[dict], config: DetectionConfig) -> list[IssueGroup]:
    groups: list[IssueGroup] = []
    meta_by = {m["name"]: m for m in metas}
    for col in df.columns:
        et = meta_by.get(col, {}).get("effective_type", "text")
        series = df[col].astype(str)
        pairs = [(int(i), v) for i, v in zip(df.index.tolist(), series.tolist()) if v.strip()]
        if et == "date":
            families: dict[str, int] = Counter()
            rids: list[int] = []
            impossible: list[tuple[int, str]] = []
            for rid, v in pairs:
                fam, fmt, dt, amb, has_time = classify_date(v, config.dayfirst_default)
                if dt is None and fam is None:
                    # maybe impossible date that matched pattern-ish
                    if any(ch.isdigit() for ch in v):
                        impossible.append((rid, v))
                    continue
                if fam:
                    families[fam] += 1
                    target = config.date_output_format
                    already = False
                    try:
                        already = bool(fmt) and dt is not None and dt.strftime(target) == v.strip()
                    except Exception:
                        already = False
                    if not already:
                        rids.append(rid)
            if len([k for k, c in families.items() if c]) >= 2:
                parts = ", ".join(f"{c}× {k}" for k, c in families.items())
                groups.append(
                    IssueGroup(
                        key=f"inconsistent_format:date_mixed:{col}",
                        type="inconsistent_format",
                        subtype="date_mixed",
                        column=col,
                        columns=[col],
                        severity="warning",
                        rids=rids,
                        cells=len(rids),
                        reason=f"Dates use {len(families)} different formats: {parts}",
                        evidence=[Evidence(rid=r, column=col, value=series.loc[r], note="format") for r in rids[:5]],
                        suggested_next_step=f"Rewrite dates to {config.date_output_format}",
                        stats={"families": dict(families)},
                        rid_count=len(rids),
                    )
                )
            if impossible:
                groups.append(
                    IssueGroup(
                        key=f"invalid_value:date:{col}",
                        type="invalid_value",
                        subtype="date",
                        column=col,
                        columns=[col],
                        severity="error",
                        rids=[r for r, _ in impossible],
                        cells=len(impossible),
                        reason=f"{impossible[0][1]} is not a real date.",
                        evidence=[Evidence(rid=r, column=col, value=v, note="impossible") for r, v in impossible[:5]],
                        suggested_next_step="Correct the date by hand — we will not guess it",
                        rid_count=len(impossible),
                    )
                )
        if et in {"integer", "decimal"}:
            mixed = []
            for rid, v in pairs:
                _, flags = clean_numeric_token(v)
                if any(flags.values()) and parse_number(v) is not None:
                    mixed.append(rid)
            if mixed:
                groups.append(
                    IssueGroup(
                        key=f"inconsistent_format:number_format:{col}",
                        type="inconsistent_format",
                        subtype="number_format",
                        column=col,
                        columns=[col],
                        severity="info",
                        rids=mixed,
                        cells=len(mixed),
                        reason="Numbers mix currency symbols, commas, or percent signs.",
                        evidence=[Evidence(rid=r, column=col, value=series.loc[r], note="format") for r in mixed[:5]],
                        suggested_next_step="Strip formatting so the numbers are comparable",
                        rid_count=len(mixed),
                    )
                )
        if et == "boolean":
            fams: dict[str, int] = Counter()
            rids = []
            for rid, v in pairs:
                t = v.strip().lower()
                for name, tokens in BOOL_FAMILIES.items():
                    if t in tokens:
                        fams[name] += 1
                        rids.append(rid)
            if len(fams) >= 2:
                groups.append(
                    IssueGroup(
                        key=f"inconsistent_format:boolean_variant:{col}",
                        type="inconsistent_format",
                        subtype="boolean_variant",
                        column=col,
                        columns=[col],
                        severity="info",
                        rids=rids,
                        cells=len(rids),
                        reason="Yes/No style values mix different spellings.",
                        evidence=[Evidence(rid=r, column=col, value=series.loc[r], note="bool") for r in rids[:5]],
                        suggested_next_step="Unify to the most common spelling",
                        rid_count=len(rids),
                    )
                )
    return groups
