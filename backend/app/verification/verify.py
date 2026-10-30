from __future__ import annotations

from collections import defaultdict

from app.core.schemas import IssueGroup
from app.verification.scoring import quality_scores


def _finding_set(groups: list[IssueGroup]) -> dict[str, set[int]]:
    out: dict[str, set[int]] = defaultdict(set)
    for g in groups:
        out[g.key].update(g.rids)
    return out


def verify(
    before_groups: list[IssueGroup],
    after_groups: list[IssueGroup],
    before_rows: int,
    after_rows: int,
    n_cols: int,
    rules_before: list[dict],
    rules_after: list[dict],
    actions: dict,
    head_seq: int,
) -> dict:
    bset = _finding_set(before_groups)
    aset = _finding_set([g for g in after_groups if g.status == "open"])
    dismissed = _finding_set([g for g in after_groups if g.status == "dismissed"])
    keys = set(bset) | set(aset) | set(dismissed)
    by_type: dict[str, dict] = {}
    groups_out = []
    for key in sorted(keys):
        typ = key.split(":")[0]
        before = bset.get(key, set())
        after = aset.get(key, set())
        disc = dismissed.get(key, set())
        resolved = before - after - disc
        remaining = before & after
        new = after - before
        rec = {
            "key": key,
            "type": typ,
            "before": len(before),
            "resolved": len(resolved),
            "dismissed": len(disc),
            "remaining": len(remaining),
            "new": len(new),
        }
        groups_out.append({**rec, "status": "remaining" if remaining else ("new" if new else "resolved")})
        slot = by_type.setdefault(typ, {"type": typ, "before": 0, "resolved": 0, "dismissed": 0, "remaining": 0, "new": 0})
        for k in ("before", "resolved", "dismissed", "remaining", "new"):
            slot[k] += rec[k]

    bscore = quality_scores(before_rows, n_cols, before_groups)
    ascore = quality_scores(after_rows, n_cols, [g for g in after_groups if g.status == "open"])
    rules_pass_b = sum(1 for r in rules_before if r.get("passed"))
    rules_pass_a = sum(1 for r in rules_after if r.get("passed"))
    open_after = ascore["open_findings"]
    open_before = bscore["open_findings"]
    all_rules_pass = rules_pass_a == len(rules_after) or not rules_after
    if open_after == 0 and all_rules_pass:
        verdict = "clean"
    elif open_after < open_before:
        verdict = "improved"
    else:
        verdict = "not_improved"
    return {
        "head_seq": head_seq,
        "verdict": verdict,
        "before": {
            "rows": before_rows,
            "open_findings": open_before,
            "quality_score": bscore["quality_score"],
            "cell_quality": bscore["cell_quality"],
            "rules_passing": rules_pass_b,
            "rules_total": len(rules_before),
        },
        "after": {
            "rows": after_rows,
            "open_findings": open_after,
            "quality_score": ascore["quality_score"],
            "cell_quality": ascore["cell_quality"],
            "rules_passing": rules_pass_a,
            "rules_total": len(rules_after),
        },
        "rows_removed": max(before_rows - after_rows, 0),
        "rows_retained_pct": round(100 * after_rows / max(before_rows, 1), 1),
        "by_type": list(by_type.values()),
        "groups": groups_out,
        "rules": [
            {
                "id": r["rule"]["id"],
                "name": r["rule"]["name"],
                "violations_before": next((x["violations"] for x in rules_before if x["rule"]["id"] == r["rule"]["id"]), 0),
                "violations_after": r["violations"],
                "unevaluable_after": r.get("unevaluable", 0),
            }
            for r in rules_after
        ],
        "actions": actions,
        "unresolved": [
            {"key": g.key, "title": g.reason, "type": g.type, "cells": g.cells, "column": g.column}
            for g in after_groups
            if g.status == "open"
        ][:50],
    }
