from __future__ import annotations

import re
from collections import defaultdict

import pandas as pd

from app.errors import AppError
from app.profiling.dates import EMAIL_RE, classify_date
from app.profiling.numbers import parse_number
from app.rules.models import summarize

PHONE_IN = re.compile(r"^(\+91[\-\s]?|0)?[6-9]\d{9}$")
PIN = re.compile(r"^[1-9]\d{5}$")
URL = re.compile(r"^https?://[^\s/$.?#][^\s]*$")


def _safe_regex(pattern: str) -> re.Pattern:
    if len(pattern) > 200:
        raise AppError("RULE_INVALID", "That regex is too long.", "Keep patterns under 200 characters.")
    if "(a+)+" in pattern or re.search(r"\([^)]*[+*][^)]*\)[+*]", pattern):
        raise AppError("RULE_INVALID", "That regex looks unsafe.", "Avoid nested repeating groups.")
    try:
        return re.compile(pattern)
    except re.error as e:
        raise AppError("RULE_INVALID", "That regex could not be compiled.", str(e)) from e


def _num(v: str):
    return parse_number(v)


def _date(v: str, dayfirst: bool):
    _, _, dt, _, _ = classify_date(v, dayfirst)
    return dt


def evaluate_rule(df: pd.DataFrame, rule, dayfirst: bool = True) -> dict:
    rids_v: list[int] = []
    uneval = 0
    reasons: dict[int, str] = {}
    columns: list[str] = []
    enabled = getattr(rule, "enabled", True)
    if not enabled:
        return {
            "rule": rule.model_dump(),
            "evaluated": 0,
            "violations": 0,
            "unevaluable": 0,
            "rids": [],
            "passed": True,
            "enabled": False,
            "columns": [],
            "summary": summarize(rule),
            "reasons": {},
        }

    t = rule.type
    if t == "range":
        columns = [rule.column]
        for rid, v in zip(df.index.tolist(), df[rule.column].astype(str).tolist()):
            if not v.strip():
                continue
            n = _num(v)
            if n is None:
                uneval += 1
                continue
            ok = True
            if rule.min is not None:
                ok = ok and (n >= rule.min if rule.inclusive else n > rule.min)
            if rule.max is not None:
                ok = ok and (n <= rule.max if rule.inclusive else n < rule.max)
            if not ok:
                rids_v.append(int(rid))
                reasons[int(rid)] = f"Row {int(rid)+1}: {rule.column} ({v}) is outside {rule.min}–{rule.max}."
    elif t == "not_null":
        columns = list(rule.columns)
        for col in rule.columns:
            for rid, v in zip(df.index.tolist(), df[col].astype(str).tolist()):
                if not v.strip():
                    rids_v.append(int(rid))
                    reasons[int(rid)] = f"Row {int(rid)+1}: {col} is required."
    elif t == "unique":
        columns = list(rule.columns)
        seen: dict[tuple, list[int]] = defaultdict(list)
        for rid in df.index.tolist():
            key = tuple(str(df.at[rid, c]).strip().casefold() for c in rule.columns)
            if all(not x for x in key):
                continue
            seen[key].append(int(rid))
        for key, ids in seen.items():
            if len(ids) > 1:
                rids_v.extend(ids)
                for i in ids:
                    reasons[i] = f"Row {i+1}: duplicate {', '.join(rule.columns)}."
    elif t == "allowed_values":
        columns = [rule.column]
        allowed = rule.values if rule.case_sensitive else [v.casefold() for v in rule.values]
        for rid, v in zip(df.index.tolist(), df[rule.column].astype(str).tolist()):
            if not v.strip():
                continue
            test = v.strip() if rule.case_sensitive else v.strip().casefold()
            if test not in allowed:
                rids_v.append(int(rid))
                reasons[int(rid)] = f"Row {int(rid)+1}: {v} is not an allowed value."
    elif t == "format":
        columns = [rule.column]
        if rule.preset == "email":
            rx = EMAIL_RE
        elif rule.preset == "phone_in":
            rx = PHONE_IN
        elif rule.preset == "pincode_in":
            rx = PIN
        elif rule.preset == "url":
            rx = URL
        else:
            rx = _safe_regex(rule.pattern or "^.*$")
        for rid, v in zip(df.index.tolist(), df[rule.column].astype(str).tolist()):
            if not v.strip():
                continue
            raw = v.strip()[:500]
            if rule.preset == "phone_in":
                raw = re.sub(r"[\s\-\(\)]", "", raw)
            if not rx.match(raw):
                rids_v.append(int(rid))
                reasons[int(rid)] = f"Row {int(rid)+1}: {v} is not a valid {rule.preset}."
    elif t == "compare":
        left = rule.left
        right = rule.right
        rcol = right.get("column")
        rval = right.get("value")
        columns = [left] + ([rcol] if rcol else [])
        for rid in df.index.tolist():
            a = str(df.at[rid, left])
            b = str(df.at[rid, rcol]) if rcol else str(rval or "")
            if rule.skip_blank and (not a.strip() or not b.strip()):
                continue
            if rule.value_type == "number":
                na, nb = _num(a), _num(b)
                if na is None or nb is None:
                    uneval += 1
                    continue
                aa, bb = na, nb
            elif rule.value_type == "date":
                da, db = _date(a, dayfirst), _date(b, dayfirst)
                if da is None or db is None:
                    uneval += 1
                    continue
                aa, bb = da, db
            else:
                aa, bb = a, b
            op = rule.op
            ok = {
                "eq": aa == bb,
                "ne": aa != bb,
                "lt": aa < bb,
                "lte": aa <= bb,
                "gt": aa > bb,
                "gte": aa >= bb,
                "contains": str(bb) in str(aa),
                "not_contains": str(bb) not in str(aa),
                "starts_with": str(aa).startswith(str(bb)),
                "ends_with": str(aa).endswith(str(bb)),
            }[op]
            if not ok:
                rids_v.append(int(rid))
                reasons[int(rid)] = f"Row {int(rid)+1}: {left} ({a}) is not {op} {rcol or rval} ({b})."
    elif t == "arithmetic":
        columns = [rule.target, rule.left] + ([rule.right] if isinstance(rule.right, str) else [])
        for rid in df.index.tolist():
            tv = _num(str(df.at[rid, rule.target]))
            lv = _num(str(df.at[rid, rule.left]))
            rv = _num(str(df.at[rid, rule.right])) if isinstance(rule.right, str) else float(rule.right)
            if tv is None or lv is None or rv is None:
                uneval += 1
                continue
            if rule.op == "div" and rv == 0:
                uneval += 1
                continue
            expected = {"add": lv + rv, "sub": lv - rv, "mul": lv * rv, "div": lv / rv}[rule.op]
            tol = max(rule.tolerance_abs, rule.tolerance_rel * abs(expected))
            if abs(tv - expected) > tol:
                rids_v.append(int(rid))
                reasons[int(rid)] = (
                    f"Row {int(rid)+1}: {rule.target} ({tv}) should equal {rule.left} {rule.op} {rule.right} ({expected})."
                )

    rids_v = sorted(set(rids_v))
    return {
        "rule": rule.model_dump(),
        "evaluated": int(len(df)),
        "violations": len(rids_v),
        "unevaluable": uneval,
        "rids": rids_v,
        "passed": len(rids_v) == 0,
        "enabled": True,
        "columns": columns,
        "summary": summarize(rule),
        "reasons": reasons,
        "sample_reason": next(iter(reasons.values()), ""),
    }
