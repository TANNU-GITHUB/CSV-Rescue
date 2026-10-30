from __future__ import annotations

import pandas as pd


def inject(df: pd.DataFrame, spec: dict | None = None, seed: int = 1) -> tuple[pd.DataFrame, list[dict]]:
    dirty = df.copy()
    manifest = []
    return dirty, manifest
