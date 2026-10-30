from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.core.ops import apply_patch, read_patch, state_hash
from app.core.schemas import DetectionConfig
from app.errors import AppError


@dataclass
class WorkingSet:
    session_id: str
    df: pd.DataFrame
    original: pd.DataFrame
    config: DetectionConfig
    column_meta: list[dict] = field(default_factory=list)
    cache: dict[str, Any] = field(default_factory=dict)
    head_seq: int = 0

    def hash(self) -> str:
        return state_hash(self.df)


class WorkingSetCache:
    def __init__(self, max_items: int = 8):
        self.max_items = max_items
        self._items: dict[str, WorkingSet] = {}
        self._order: list[str] = []

    def get(self, sid: str) -> WorkingSet | None:
        ws = self._items.get(sid)
        if ws:
            self._order = [s for s in self._order if s != sid] + [sid]
        return ws

    def put(self, ws: WorkingSet) -> None:
        self._items[ws.session_id] = ws
        self._order = [s for s in self._order if s != ws.session_id] + [ws.session_id]
        while len(self._order) > self.max_items:
            old = self._order.pop(0)
            self._items.pop(old, None)

    def drop(self, sid: str) -> None:
        self._items.pop(sid, None)
        self._order = [s for s in self._order if s != sid]


CACHE = WorkingSetCache()


def replay(original: pd.DataFrame, patches: list[tuple[int, Any]], expected_hash: str | None) -> pd.DataFrame:
    df = original.copy()
    for _, path in patches:
        patch = read_patch(path)
        df = apply_patch(df, patch, check=False)
    if expected_hash and state_hash(df) != expected_hash:
        raise AppError("STATE_CORRUPT", "Saved history does not match the data.", "Reset to the original file.")
    return df
