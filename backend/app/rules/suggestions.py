from __future__ import annotations

import re

from app.core.ids import new_id
from app.rules.evaluator import evaluate_rule
from app.rules.models import ArithmeticRule, CompareRule, FormatRule, RangeRule, UniqueRule, parse_rule, summarize


def suggest_rules(df, metas: list[dict], dayfirst: bool = True) -> list[dict]:
    names = [c for c in df.columns]
    lower = {c.lower(): c for c in names}
    out = []

    def add(rule):
        res = evaluate_rule(df, rule, dayfirst)
        if res["evaluated"] == 0:
            return
        out.append({"rule": rule.model_dump(), "summary": summarize(rule), "would_flag": res["violations"]})

    for col in names:
        cl = col.lower()
        if re.search(r"^age$|_age$", cl):
            add(RangeRule(id=new_id(6), name=f"{col} 0–120", column=col, min=0, max=120, origin="suggested"))
        if re.search(r"qty|quantity|units|count|stock", cl):
            add(RangeRule(id=new_id(6), name=f"{col} ≥ 0", column=col, min=0, origin="suggested"))
        if re.search(r"price|amount|total|cost|salary|fee", cl):
            add(RangeRule(id=new_id(6), name=f"{col} ≥ 0", column=col, min=0, origin="suggested"))
        if re.search(r"percent|pct|percentage", cl):
            add(RangeRule(id=new_id(6), name=f"{col} 0–100", column=col, min=0, max=100, origin="suggested"))
        if re.search(r"rating|stars|score_?out_?of", cl):
            add(RangeRule(id=new_id(6), name=f"{col} 1–5", column=col, min=1, max=5, origin="suggested"))
        if re.search(r"marks?$|score$", cl) or cl in {"math", "science", "english", "total_marks"}:
            add(RangeRule(id=new_id(6), name=f"{col} 0–100", column=col, min=0, max=100, origin="suggested"))
        if "email" in cl:
            add(FormatRule(id=new_id(6), name=f"{col} is email", column=col, preset="email", origin="suggested"))
        if re.search(r"phone|mobile|contact", cl):
            add(FormatRule(id=new_id(6), name=f"{col} is phone", column=col, preset="phone_in", origin="suggested"))
        if re.search(r"pin(code)?|zip|postal", cl):
            add(FormatRule(id=new_id(6), name=f"{col} is pincode", column=col, preset="pincode_in", origin="suggested"))
        if re.search(r"(^|_)(id|uuid|sku|code)$", cl) or cl.endswith("_id"):
            add(UniqueRule(id=new_id(6), name=f"{col} unique", columns=[col], origin="suggested"))

    def find(pat):
        return [c for c in names if re.search(pat, c.lower())]

    starts = find(r"(start|from|begin|open|issue|order)\w*date")
    ends = find(r"(end|to|close|expiry|due|delivery|ship)\w*date")
    if starts and ends:
        add(
            CompareRule(
                id=new_id(6),
                name=f"{starts[0]} ≤ {ends[0]}",
                left=starts[0],
                op="lte",
                right={"column": ends[0]},
                value_type="date",
                origin="suggested",
            )
        )
    totals = find(r"total|line_total")
    qtys = find(r"qty|quantity")
    prices = find(r"unit_?price|price|rate")
    if totals and qtys and prices:
        add(
            ArithmeticRule(
                id=new_id(6),
                name=f"{totals[0]} = {qtys[0]} × {prices[0]}",
                target=totals[0],
                left=qtys[0],
                op="mul",
                right=prices[0],
                origin="suggested",
            )
        )
    return out
