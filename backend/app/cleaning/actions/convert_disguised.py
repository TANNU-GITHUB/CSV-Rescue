from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec


class ConvertDisguisedMissing(Action):
    id = "convert_disguised_missing"
    priority = 15

    def applies(self, issue) -> bool:
        return issue.type == "missing_value" and issue.subtype == "disguised"

    def param_schema(self):
        return [ParamSpec(name="tokens", label="Tokens", kind="text", default="na,n/a,-")]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        tokens = {t.strip().lower() for t in str(params.get("tokens", "na,n/a,-,null,none,nan,?,--")).split(",")}
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col])
            if before.strip().lower() in tokens:
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after="",
                        reason="Placeholder converted to blank",
                        confidence=0.8,
                        selected=True,
                    )
                )
        return out

    def title(self, column, n):
        return f"Convert placeholders to blank in {column}"

    def explanation(self, column, n, params):
        return f"Set placeholder tokens to blank in {n} cells. A token like 'None' might be a real category — review required."

    def risk(self, params):
        return "review"
