from __future__ import annotations


def explain_issue(issue: dict) -> dict:
    t = issue.get("type")
    col = issue.get("column") or "this column"
    n = issue.get("cells") or issue.get("rid_count") or 0
    templates = {
        "missing_value": {
            "summary": f"{n} values in {col} are blank or placeholders.",
            "why_it_matters": "Blank cells break totals, joins and charts. Decide whether to fill, leave, or drop those rows.",
            "suggested_action": "Open Cleaning Studio and pick a fill strategy — nothing is applied until you accept.",
        },
        "duplicate_row": {
            "summary": f"{n} rows are exact copies of earlier rows.",
            "why_it_matters": "Duplicates inflate counts. Removing them deletes data, so you must confirm.",
            "suggested_action": "Keep the first copy and delete extras if they really are repeats.",
        },
        "inconsistent_text": {
            "summary": f"Text in {col} is written in more than one way ({n} cells).",
            "why_it_matters": "Filters and group-bys treat 'Jaipur' and 'jaipur' as different places.",
            "suggested_action": "Trim spaces and standardise capitalisation first (safe). Review lookalikes separately.",
        },
        "inconsistent_format": {
            "summary": f"{col} mixes formats in {n} cells.",
            "why_it_matters": "Dates and numbers only sort and calculate when they share one format.",
            "suggested_action": "Standardise to a single format. Ambiguous dates stay on review.",
        },
        "invalid_numeric": {
            "summary": f"{n} values in {col} are not numbers (for example 'twenty').",
            "why_it_matters": "Those cells cannot be summed until they become digits.",
            "suggested_action": "Convert number words where we can, otherwise clear or fix by hand.",
        },
        "invalid_value": {
            "summary": f"{n} rows break a rule involving {col}.",
            "why_it_matters": "Rules catch impossible combinations that single-column checks miss.",
            "suggested_action": "Read the reason on each row, then pick a fix or mark the row as valid.",
        },
        "outlier": {
            "summary": f"{n} values in {col} sit far from the rest. Suspicious, not necessarily wrong.",
            "why_it_matters": "A giant quantity can be a typo — or a real bulk order. We never auto-delete outliers.",
            "suggested_action": "Inspect the rows. Keep, blank, clip, or exclude only if you mean to.",
        },
        "duplicate_id": {
            "summary": f"The same identifier in {col} appears on {n} rows.",
            "why_it_matters": "IDs should point to one record. Auto-merging could hide two real people.",
            "suggested_action": "Compare the conflicting rows side by side and choose which to keep.",
        },
    }
    return templates.get(t, {"summary": issue.get("reason") or "Issue found.", "why_it_matters": "Worth a look.", "suggested_action": "Review in the studio."})


def review_cluster(values: list[str]) -> dict:
    return {
        "verdict": "unsure",
        "confidence": 0.5,
        "reasoning": "Spelling similarity is high. We can't tell if they are the same — please review.",
    }


def summarize_verification(v: dict) -> str:
    a = v.get("after", {})
    b = v.get("before", {})
    return (
        f"Quality moved from {b.get('quality_score')} to {a.get('quality_score')}. "
        f"Open findings went from {b.get('open_findings')} to {a.get('open_findings')}. "
        f"Verdict: {v.get('verdict')}."
    )


def parse_nl_rule(text: str, columns: list[str]) -> dict | None:
    import re

    t = text.lower()
    colmap = {c.lower(): c for c in columns}

    def col_near(word):
        for k, v in colmap.items():
            if k in word or word in k:
                return v
        return None

    m = re.search(r"(\w+)\s+must be between\s+([0-9.]+)\s+and\s+([0-9.]+)", t)
    if m:
        c = col_near(m.group(1)) or m.group(1)
        if c in columns or c in colmap.values():
            return {"type": "range", "name": text, "column": c if c in columns else colmap.get(c, c), "min": float(m.group(2)), "max": float(m.group(3))}
    m = re.search(r"(\w+)\s+should be greater than\s+(\w+)", t)
    if m:
        a, b = col_near(m.group(1)), col_near(m.group(2))
        if a and b:
            return {"type": "compare", "name": text, "left": a, "op": "gt", "right": {"column": b}, "value_type": "number"}
    m = re.search(r"(\w+)\s*=\s*(\w+)\s*\*\s*(\w+)", t)
    if m:
        a, b, c = col_near(m.group(1)), col_near(m.group(2)), col_near(m.group(3))
        if a and b and c:
            return {"type": "arithmetic", "name": text, "target": a, "left": b, "op": "mul", "right": c}
    if "unique" in t:
        for c in columns:
            if c.lower() in t:
                return {"type": "unique", "name": text, "columns": [c]}
    if "required" in t or "not null" in t or "must not be blank" in t:
        for c in columns:
            if c.lower() in t:
                return {"type": "not_null", "name": text, "columns": [c]}
    return None
