from collections import defaultdict

from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec


class ResolveDuplicateIds(Action):
    id = "resolve_duplicate_ids"
    priority = 80

    def applies(self, issue) -> bool:
        return issue.type == "duplicate_id"

    def param_schema(self):
        return [
            ParamSpec(
                name="mode",
                label="Keep",
                kind="select",
                options=["keep_all", "keep_first", "keep_last"],
                default="keep_all",
            )
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        mode = params.get("mode", "keep_all")
        if mode == "keep_all":
            return []
        col = issue.column
        buckets: dict[str, list[int]] = defaultdict(list)
        for rid in issue.rids:
            buckets[str(df.at[rid, col]).strip().casefold()].append(int(rid))
        out = []
        for ids in buckets.values():
            if len(ids) < 2:
                continue
            keep = ids[0] if mode == "keep_first" else ids[-1]
            for rid in ids:
                if rid == keep:
                    continue
                out.append(
                    Change(
                        id=f"row:{rid}",
                        kind="row_delete",
                        rid=rid,
                        column=None,
                        before=None,
                        after=None,
                        reason="Duplicate identifier — extra row removed",
                        confidence=0.5,
                        selected=False,
                    )
                )
        return out

    def title(self, column, n):
        return f"Resolve duplicate {column} values"

    def explanation(self, column, n, params):
        return "Different records may share an ID — review. Nothing is deleted unless you choose a keep strategy."

    def risk(self, params):
        return "destructive"
