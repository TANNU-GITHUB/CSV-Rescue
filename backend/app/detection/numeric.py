from __future__ import annotations

import pandas as pd

from app.core.schemas import DetectionConfig, Evidence, IssueGroup
from app.profiling.number_words import words_to_number
from app.profiling.numbers import parse_number


def detect_invalid_numeric(df: pd.DataFrame, metas: list[dict], config: DetectionConfig) -> list[IssueGroup]:
    tokens = {t.lower() for t in config.missing_tokens}
    groups: list[IssueGroup] = []
    meta_by = {m["name"]: m for m in metas}
    for col in df.columns:
        et = meta_by.get(col, {}).get("effective_type")
        if et not in {"integer", "decimal"}:
            continue
        bad: list[tuple[int, str]] = []
        words: list[str] = []
        for rid, v in zip(df.index.tolist(), df[col].astype(str).tolist()):
            s = v
            if s.strip() == "" or s.strip().lower() in tokens:
                continue
            if parse_number(s) is None:
                bad.append((int(rid), s))
                if words_to_number(s) is not None:
                    words.append(s)
        if bad:
            groups.append(
                IssueGroup(
                    key=f"invalid_numeric:parse:{col}",
                    type="invalid_numeric",
                    subtype="parse",
                    column=col,
                    columns=[col],
                    severity="error",
                    rids=[r for r, _ in bad],
                    cells=len(bad),
                    reason=f'{col} = "{bad[0][1]}" is not a number',
                    evidence=[Evidence(rid=r, column=col, value=v, note="invalid") for r, v in bad[:5]],
                    suggested_next_step="Convert number words or set the cell blank",
                    stats={"parsable_as_words": words},
                    rid_count=len(bad),
                )
            )
    return groups
