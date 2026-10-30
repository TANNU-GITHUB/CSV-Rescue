from collections import Counter

from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec

MAPS = {
    "Yes/No": {"true": "Yes", "yes": "Yes", "y": "Yes", "1": "Yes", "t": "Yes", "false": "No", "no": "No", "n": "No", "0": "No", "f": "No"},
    "Y/N": {"true": "Y", "yes": "Y", "y": "Y", "1": "Y", "t": "Y", "false": "N", "no": "N", "n": "N", "0": "N", "f": "N"},
    "true/false": {"true": "true", "yes": "true", "y": "true", "1": "true", "t": "true", "false": "false", "no": "false", "n": "false", "0": "false", "f": "false"},
    "1/0": {"true": "1", "yes": "1", "y": "1", "1": "1", "t": "1", "false": "0", "no": "0", "n": "0", "0": "0", "f": "0"},
}


class NormalizeBooleans(Action):
    id = "normalize_booleans"
    priority = 26

    def applies(self, issue) -> bool:
        return issue.type == "inconsistent_format" and issue.subtype == "boolean_variant"

    def param_schema(self):
        return [ParamSpec(name="target", label="Target spelling", kind="select", options=list(MAPS), default="Yes/No")]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        target = params.get("target", "Yes/No")
        mapping = MAPS.get(target, MAPS["Yes/No"])
        out = []
        for rid in issue.rids:
            before = str(df.at[rid, col])
            after = mapping.get(before.strip().lower())
            if after is not None and after != before:
                out.append(
                    Change(
                        id=f"{rid}:{col}",
                        kind="cell_update",
                        rid=int(rid),
                        column=col,
                        before=before,
                        after=after,
                        reason="Boolean spelling unified",
                        confidence=1.0,
                        selected=True,
                    )
                )
        return out

    def title(self, column, n):
        return f"Unify Yes/No values in {column}"

    def explanation(self, column, n, params):
        return f"Rewrite mixed boolean spellings to one family in {n} cells."

    def risk(self, params):
        return "safe"
