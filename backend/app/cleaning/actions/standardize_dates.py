from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec
from app.profiling.dates import classify_date


class StandardizeDates(Action):
    id = "standardize_dates"
    priority = 30

    def applies(self, issue) -> bool:
        return issue.type == "inconsistent_format" and issue.subtype == "date_mixed"

    def param_schema(self):
        return [
            ParamSpec(name="dayfirst", label="Day first", kind="toggle", default=True),
            ParamSpec(name="output_format", label="Output format", kind="text", default="%Y-%m-%d"),
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        dayfirst = params.get("dayfirst", True)
        fmt = params.get("output_format", "%Y-%m-%d")
        out = []
        any_ambiguous = False
        for rid in df.index.tolist() if not issue else issue.rids:
            before = str(df.at[rid, col])
            if not before.strip():
                continue
            fam, f, dt, amb, has_time = classify_date(before, dayfirst)
            if dt is None:
                continue
            after = dt.strftime(fmt)
            if after == before:
                continue
            if amb:
                any_ambiguous = True
            conf = 0.7 if amb else 1.0
            out.append(
                Change(
                    id=f"{rid}:{col}",
                    kind="cell_update",
                    rid=int(rid),
                    column=col,
                    before=before,
                    after=after,
                    reason="Date rewritten to a single format",
                    confidence=conf,
                    selected=not amb,
                )
            )
        self._ambiguous = any_ambiguous
        return out

    def title(self, column, n):
        return f"Standardise dates in {column}"

    def explanation(self, column, n, params):
        extra = ""
        if not params.get("dayfirst", True) is False:
            extra = " Dates like 03/04/2026 can mean 3 April or 4 March. We assumed day-first — change it here."
        return f"Rewrite dates to {params.get('output_format', '%Y-%m-%d')} in {n} cells.{extra}"

    def risk(self, params):
        return "review"
