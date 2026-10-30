from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec
from app.profiling.numbers import clean_numeric_token, parse_number


class NormalizeNumbers(Action):
    id = "normalize_numbers"
    priority = 25

    def applies(self, issue) -> bool:
        return issue.type == "inconsistent_format" and issue.subtype == "number_format"

    def param_schema(self):
        return [
            ParamSpec(
                name="keep_percent_as",
                label="Percents become",
                kind="select",
                options=["whole", "fraction"],
                default="whole",
            )
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        mode = params.get("keep_percent_as", "whole")
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col])
            token, flags = clean_numeric_token(before)
            n = parse_number(before)
            if n is None:
                continue
            if flags.get("percent") and mode == "fraction":
                n = n / 100.0
            after = str(int(n)) if float(n).is_integer() else str(n)
            if after != before:
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after=after,
                        reason="Number formatting stripped",
                        confidence=0.85 if flags.get("percent") else 1.0,
                        selected=True,
                    )
                )
        return out

    def title(self, column, n):
        return f"Normalise numbers in {column}"

    def explanation(self, column, n, params):
        return f"Strip currency symbols, thousands separators and similar formatting in {n} cells."

    def risk(self, params):
        return "review" if params.get("keep_percent_as") == "fraction" else "safe"
