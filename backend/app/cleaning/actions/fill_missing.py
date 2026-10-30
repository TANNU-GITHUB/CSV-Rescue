from collections import Counter

import numpy as np

from app.cleaning.base import Action
from app.core.schemas import AlternativeAction, Change, ParamSpec
from app.profiling.numbers import parse_number


class FillMissing(Action):
    id = "fill_missing"
    priority = 50

    def applies(self, issue) -> bool:
        return issue.type == "missing_value" and issue.subtype == "blank"

    def param_schema(self):
        return [
            ParamSpec(
                name="strategy",
                label="Strategy",
                kind="select",
                options=["leave", "median", "mean", "mode", "constant", "drop_rows"],
                default="mode",
            ),
            ParamSpec(name="constant", label="Fixed value", kind="text", default=""),
        ]

    def alternatives(self):
        return [
            AlternativeAction(action="fill_missing", title="Fill with median", params={"strategy": "median"}),
            AlternativeAction(action="fill_missing", title="Fill with mean", params={"strategy": "mean"}),
            AlternativeAction(action="fill_missing", title="Fill with mode", params={"strategy": "mode"}),
            AlternativeAction(action="fill_missing", title="Remove rows", params={"strategy": "drop_rows"}),
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        strategy = params.get("strategy", "leave")
        if strategy == "leave":
            return []
        nums = [parse_number(v) for v in df[col].astype(str).tolist() if parse_number(v) is not None]
        fill = ""
        if strategy == "median" and nums:
            m = float(np.median(nums))
            fill = str(int(m)) if m.is_integer() else str(m)
        elif strategy == "mean" and nums:
            m = float(np.mean(nums))
            fill = str(round(m, 2))
        elif strategy == "mode":
            c = Counter(v for v in df[col].astype(str).tolist() if v.strip())
            fill = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if c else ""
        elif strategy == "constant":
            fill = str(params.get("constant", ""))
        out = []
        for rid in issue.rids:
            if strategy == "drop_rows":
                out.append(
                    Change(
                        id=f"row:{rid}",
                        kind="row_delete",
                        rid=int(rid),
                        column=None,
                        before=None,
                        after=None,
                        reason="Row removed because a required value was blank",
                        confidence=0.7,
                        selected=False,
                    )
                )
            else:
                before = str(df.at[rid, col])
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after=fill,
                        reason="Filled missing value (invented — review)",
                        confidence=0.6,
                        selected=True,
                    )
                )
        return out

    def title(self, column, n):
        return f"Fill missing values in {column}"

    def explanation(self, column, n, params):
        return (
            f"Filling invents values for {n} blank cells. It keeps the row but can bias averages. "
            "You can also leave the blanks or remove the rows."
        )

    def risk(self, params):
        if params.get("strategy") == "drop_rows":
            return "destructive"
        if params.get("strategy") in {"leave", None}:
            return "review"
        return "review"
