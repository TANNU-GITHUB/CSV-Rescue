from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec
from app.profiling.numbers import parse_number


class FixOutOfRange(Action):
    id = "fix_out_of_range"
    priority = 60

    def applies(self, issue) -> bool:
        return issue.type == "invalid_value" and str(issue.subtype).startswith("rule:")

    def param_schema(self):
        return [
            ParamSpec(
                name="mode",
                label="Fix",
                kind="select",
                options=["set_blank", "clip_to_bound", "leave", "delete_rows"],
                default="set_blank",
            )
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        mode = params.get("mode", "set_blank")
        if mode == "leave":
            return []
        col = issue.column
        mx = (issue.stats or {}).get("max")
        mn = (issue.stats or {}).get("min")
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col]) if col else ""
            if mode == "delete_rows":
                out.append(
                    Change(
                        id=f"row:{rid}",
                        kind="row_delete",
                        rid=int(rid),
                        column=None,
                        before=None,
                        after=None,
                        reason="Row removed due to rule violation",
                        confidence=0.5,
                        selected=False,
                    )
                )
                continue
            n = parse_number(before)
            after = ""
            if mode == "clip_to_bound" and n is not None:
                if mx is not None and n > mx:
                    after = str(mx)
                elif mn is not None and n < mn:
                    after = str(mn)
                else:
                    after = before
            out.append(
                Change(
                    id=f"{rid}:{col}",
                    kind="cell_update",
                    rid=int(rid),
                    column=col,
                    before=before,
                    after=after,
                    reason="Rule violation adjusted",
                    confidence=0.6,
                    selected=True,
                )
            )
        return out

    def title(self, column, n):
        return f"Fix rule violations in {column or 'rows'}"

    def explanation(self, column, n, params):
        return f"Apply a chosen fix to {n} rule violations."

    def risk(self, params):
        return "destructive" if params.get("mode") == "delete_rows" else "review"


class FixRuleViolation(FixOutOfRange):
    id = "fix_rule_violation"
    priority = 62
