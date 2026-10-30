from collections import Counter

from app.cleaning.base import Action
from app.core.schemas import Change, ParamSpec
from app.detection.text import _norm


class NormalizeCaseVariants(Action):
    id = "normalize_case_variants"
    priority = 20

    def applies(self, issue) -> bool:
        return issue.type == "inconsistent_text" and issue.subtype == "case_variant"

    def param_schema(self):
        return [
            ParamSpec(
                name="canonical",
                label="Canonical form",
                kind="select",
                options=["most_frequent", "title", "upper", "lower"],
                default="most_frequent",
            )
        ]

    def build_changes(self, df, params, issue=None, **kwargs):
        col = issue.column
        mode = params.get("canonical", "most_frequent")
        buckets: dict[str, list[tuple[int, str]]] = {}
        for rid in issue.rids:
            v = str(df.at[rid, col])
            buckets.setdefault(_norm(v), []).append((int(rid), v))
        out = []
        for forms in buckets.values():
            counts = Counter(v for _, v in forms)
            most = counts.most_common(1)[0][0]
            if mode == "title":
                canon = most.strip().title()
            elif mode == "upper":
                canon = most.strip().upper()
            elif mode == "lower":
                canon = most.strip().lower()
            else:
                canon = most.strip()
                # tie -> title
            for rid, before in forms:
                if before != canon:
                    out.append(
                        Change(
                            id=f"{rid}:{col}",
                            kind="cell_update",
                            rid=rid,
                            column=col,
                            before=before,
                            after=canon,
                            reason="Capitalisation standardised",
                            confidence=1.0,
                            selected=True,
                        )
                    )
        return out

    def title(self, column, n):
        return f"Standardise capitalisation in {column}"

    def explanation(self, column, n, params):
        return f"Map case variants to a single spelling in {n} cells."

    def risk(self, params):
        return "safe"
