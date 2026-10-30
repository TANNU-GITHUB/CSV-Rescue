from __future__ import annotations

import pandas as pd

from app.core.schemas import Evidence, IssueGroup


def groups_from_rule_results(results: list[dict], df: pd.DataFrame) -> list[IssueGroup]:
    out: list[IssueGroup] = []
    for res in results:
        if not res.get("enabled", True):
            continue
        rids = [int(x) for x in res.get("rids") or []]
        if not rids:
            continue
        rid_rule = res["rule"]
        cols = res.get("columns") or []
        col = cols[0] if cols else None
        samples = []
        for rid in rids[:5]:
            val = ""
            if col and col in df.columns and rid in df.index:
                val = str(df.at[rid, col])
            samples.append(Evidence(rid=rid, column=col or "*", value=val, note=res.get("sample_reason") or ""))
        out.append(
            IssueGroup(
                key=f"invalid_value:rule:{rid_rule['id']}",
                type="invalid_value",
                subtype=f"rule:{rid_rule['id']}",
                column=col,
                columns=cols,
                severity=rid_rule.get("severity", "error"),
                rids=rids,
                cells=len(rids),
                reason=res.get("summary") or rid_rule.get("description") or "Rule violation",
                evidence=samples,
                suggested_next_step="Open the rule violation in Cleaning Studio",
                stats={"unevaluable": res.get("unevaluable", 0)},
                rid_count=len(rids),
            )
        )
    return out
