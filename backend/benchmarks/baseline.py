from __future__ import annotations

import pandas as pd


def naive_clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        out[c] = out[c].astype(str).str.strip()
    out = out.drop_duplicates()
    return out
