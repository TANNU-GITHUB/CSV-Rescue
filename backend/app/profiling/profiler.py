from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.schemas import ColumnMeta, DetectionConfig
from app.profiling.dates import classify_date
from app.profiling.numbers import parse_number
from app.profiling.type_infer import infer_column


def _missing_counts(series: pd.Series, tokens: set[str]) -> tuple[int, int]:
    blank = 0
    disguised = 0
    for v in series:
        s = str(v)
        if s.strip() == "":
            blank += 1
        elif s.strip().lower() in tokens:
            disguised += 1
    return blank, disguised


def profile_dataframe(df: pd.DataFrame, config: DetectionConfig) -> dict[str, Any]:
    tokens = set(t.lower() for t in config.missing_tokens)
    columns: list[dict] = []
    metas: list[ColumnMeta] = []
    total_missing = 0
    for col in df.columns:
        series = df[col].astype(str)
        nonblank = [v for v in series if v.strip() != ""]
        inferred, conf, _ = infer_column(col, nonblank, config)
        override = config.type_overrides.get(col)
        effective = override or inferred
        blank, disguised = _missing_counts(series, tokens)
        total_missing += blank + disguised
        distinct = series.nunique(dropna=False)
        top = series.value_counts().head(5)
        samples = nonblank[:5]
        card: dict[str, Any] = {
            "name": col,
            "inferred_type": inferred,
            "effective_type": effective,
            "type_confidence": round(conf, 4),
            "missing_blank": blank,
            "missing_disguised": disguised,
            "missing_pct": round(100 * (blank + disguised) / max(len(df), 1), 2),
            "distinct": int(distinct),
            "unique": bool(distinct == len(df) and blank == 0),
            "samples": samples,
            "top_values": [{"value": str(i), "count": int(c)} for i, c in top.items()],
        }
        nums = [parse_number(v) for v in nonblank]
        nums_ok = [x for x in nums if x is not None]
        if effective in {"integer", "decimal"} and nums_ok:
            arr = np.array(nums_ok, dtype=float)
            card["numeric"] = {
                "min": float(arr.min()),
                "max": float(arr.max()),
                "mean": float(arr.mean()),
                "median": float(np.median(arr)),
                "std": float(arr.std()) if len(arr) > 1 else 0.0,
                "q1": float(np.percentile(arr, 25)),
                "q3": float(np.percentile(arr, 75)),
            }
            hist, edges = np.histogram(arr, bins=10)
            card["histogram"] = [{"bin": float(edges[i]), "count": int(hist[i])} for i in range(len(hist))]
        if effective in {"text", "category"}:
            lens = [len(v) for v in nonblank] or [0]
            card["text"] = {"min_len": min(lens), "max_len": max(lens), "avg_len": sum(lens) / len(lens)}
        if effective == "date":
            dts = []
            formats: dict[str, int] = {}
            for v in nonblank:
                fam, fmt, dt, _, _ = classify_date(v, config.dayfirst_default)
                if fmt:
                    formats[fmt] = formats.get(fmt, 0) + 1
                if dt:
                    dts.append(dt)
            card["date"] = {
                "earliest": min(dts).date().isoformat() if dts else None,
                "latest": max(dts).date().isoformat() if dts else None,
                "formats": [{"format": k, "count": v} for k, v in formats.items()],
            }
        unique_auto = effective == "id"
        meta = ColumnMeta(
            name=col,
            inferred_type=inferred,
            type_confidence=conf,
            override_type=override,
            effective_type=effective,
            is_unique_declared=col in config.unique_columns,
            unique_auto=unique_auto,
        )
        metas.append(meta)
        card["open_issues"] = 0
        columns.append(card)

    dup_count = int(df.duplicated(keep="first").sum())
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "total_cells": int(df.size),
        "missing_cells": total_missing,
        "duplicate_rows": dup_count,
        "column_cards": columns,
        "column_meta": [m.model_dump() for m in metas],
    }
