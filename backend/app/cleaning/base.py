from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.schemas import AlternativeAction, Change, ParamSpec, Proposal


class Action:
    id: str = ""
    priority: int = 50

    def applies(self, issue) -> bool:
        return False

    def build_changes(self, df: pd.DataFrame, params: dict[str, Any], issue=None, **kwargs) -> list[Change]:
        return []

    def param_schema(self) -> list[ParamSpec]:
        return []

    def alternatives(self) -> list[AlternativeAction]:
        return []

    def title(self, column: str | None, n: int) -> str:
        return self.id

    def explanation(self, column: str | None, n: int, params: dict) -> str:
        return ""

    def risk(self, params: dict) -> str:
        return "safe"
