from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec


class RemoveDuplicateRows(Action):
    id = "remove_duplicate_rows"
    priority = 40

    def applies(self, issue) -> bool:
        return issue.type == "duplicate_row"

    def param_schema(self):
        return [ParamSpec(name="keep", label="Keep", kind="select", options=["first", "last"], default="first")]

    def build_changes(self, df, params, issue=None, **kwargs):
        keep = params.get("keep", "first")
        rids = list(issue.rids)
        if keep == "last":
            # invert: delete first copies instead
            cols = list(df.columns)
            mask = df.duplicated(subset=cols, keep="last")
            rids = [int(i) for i in df.index[mask].tolist()]
        out = []
        for rid in rids:
            out.append(
                Change(
                    id=f"row:{rid}",
                    kind="row_delete",
                    rid=int(rid),
                    column=None,
                    before=None,
                    after=None,
                    reason="Redundant duplicate row",
                    confidence=1.0,
                    selected=True,
                )
            )
        return out

    def title(self, column, n):
        return f"Remove {n} duplicate rows"

    def explanation(self, column, n, params):
        return f"Removing {n} rows discards their values in all columns. You can undo this."

    def risk(self, params):
        return "destructive"
