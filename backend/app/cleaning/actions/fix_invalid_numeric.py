from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec
from app.profiling.number_words import words_to_number


class FixInvalidNumeric(Action):
    id = "fix_invalid_numeric"
    priority = 45

    def applies(self, issue) -> bool:
        return issue.type == "invalid_numeric"

    def param_schema(self):
        return [
            ParamSpec(
                name="mode",
                label="How to fix",
                kind="select",
                options=["convert_words", "set_blank", "leave"],
                default="convert_words",
            )
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        mode = params.get("mode", "convert_words")
        if mode == "leave":
            return []
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col])
            if mode == "convert_words":
                n = words_to_number(before)
                if n is None:
                    continue
                after = str(n)
            else:
                after = ""
            out.append(
                Change(
                    id=f"{rid}:{col}",
                    kind="cell_update",
                    rid=int(rid),
                    column=col,
                    before=before,
                    after=after,
                    reason="Number word converted" if mode == "convert_words" else "Invalid number cleared",
                    confidence=0.85,
                    selected=True,
                )
            )
        return out

    def title(self, column, n):
        return f"Fix invalid numbers in {column}"

    def explanation(self, column, n, params):
        return f"Convert number words (like twenty → 20) or clear invalid cells in {n} rows."

    def risk(self, params):
        return "review"
