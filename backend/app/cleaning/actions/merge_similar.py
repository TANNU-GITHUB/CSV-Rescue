from collections import Counter

from rapidfuzz import fuzz

from app.cleaning.base import Action
from app.core.schemas import Change
from app.detection.text import _norm


class MergeSimilarValues(Action):
    id = "merge_similar_values"
    priority = 55

    def applies(self, issue) -> bool:
        return issue.type == "inconsistent_text" and issue.subtype == "similar_values"

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        values = [(int(rid), str(df.at[rid, col])) for rid in issue.rids]
        counts = Counter(_norm(v) for _, v in values)
        # most frequent overall as default canonical per cluster from stats if present
        canon_map = params.get("canonical_map") or {}
        # naive: map rarer to most frequent if similar
        most = counts.most_common(1)[0][0] if counts else ""
        display = {}
        for _, v in values:
            display[_norm(v)] = v
        out = []
        for rid, before in values:
            key = _norm(before)
            target_key = canon_map.get(key, most)
            after = display.get(target_key, before)
            if after == before:
                continue
            sim = fuzz.ratio(key, target_key) / 100
            out.append(
                Change(
                    id=f"{rid}:{col}",
                    kind="cell_update",
                    rid=rid,
                    column=col,
                    before=before,
                    after=after,
                    reason=f"Possible spelling variation ({int(sim*100)}% similar to '{after}') — review required",
                    confidence=sim,
                    selected=False,
                )
            )
        return out

    def title(self, column, n):
        return f"Merge similar values in {column}"

    def explanation(self, column, n, params):
        return f"Map rare lookalikes to the most common spelling in {n} cells. Nothing is selected by default."

    def risk(self, params):
        return "review"
