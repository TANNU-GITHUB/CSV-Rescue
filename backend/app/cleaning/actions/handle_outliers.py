from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec


class HandleOutliers(Action):
    id = "handle_outliers"
    priority = 70

    def applies(self, issue) -> bool:
        return issue.type == "outlier"

    def param_schema(self):
        return [
            ParamSpec(
                name="mode",
                label="What to do",
                kind="select",
                options=["keep", "set_blank", "exclude_rows", "clip_to_fence"],
                default="keep",
            )
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        mode = params.get("mode", "keep")
        if mode == "keep":
            return []
        col = issue.column
        fence = (issue.stats or {}).get("q3", 0)
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col])
            if mode == "set_blank":
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after="",
                        reason="Outlier cleared — review",
                        confidence=0.4,
                        selected=False,
                    )
                )
            elif mode == "exclude_rows":
                out.append(
                    Change(
                        id=f"row:{rid}",
                        kind="row_delete",
                        rid=int(rid),
                        column=None,
                        before=None,
                        after=None,
                        reason="Row excluded as outlier",
                        confidence=0.4,
                        selected=False,
                    )
                )
            elif mode == "clip_to_fence":
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after=str(fence),
                        reason="Clipped to fence",
                        confidence=0.4,
                        selected=False,
                    )
                )
        return out

    def title(self, column, n):
        return f"Review outliers in {column}"

    def explanation(self, column, n, params):
        return f"Suspicious, not necessarily wrong. {n} values sit far from the rest. No change by default."

    def risk(self, params):
        if params.get("mode") == "exclude_rows":
            return "destructive"
        return "review"
