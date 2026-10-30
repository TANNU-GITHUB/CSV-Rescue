from __future__ import annotations

import re

from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec


def tidy(v: str, collapse: bool) -> str:
    s = v.replace("\u00a0", " ").replace("\u200b", "")
    s = s.strip()
    if collapse:
        s = re.sub(r" {2,}", " ", s)
    return s


class TrimWhitespace(Action):
    id = "trim_whitespace"
    priority = 10

    def applies(self, issue) -> bool:
        return issue.type == "inconsistent_text" and issue.subtype == "whitespace"

    def param_schema(self):
        return [ParamSpec(name="collapse_internal", label="Collapse extra spaces", kind="toggle", default=True)]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        collapse = params.get("collapse_internal", True)
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col])
            after = tidy(before, collapse)
            if after != before:
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after=after,
                        reason="Extra spaces removed",
                        confidence=1.0,
                        selected=True,
                    )
                )
        return out

    def title(self, column, n):
        return f"Trim whitespace in {column}"

    def explanation(self, column, n, params):
        return f"Trim leading and trailing whitespace in {n} cells. This standardises text without changing the words themselves."

    def risk(self, params):
        return "safe"
