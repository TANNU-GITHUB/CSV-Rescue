from __future__ import annotations

import pandas as pd

from app.core.ops import apply_patch, patch_from_changes, state_hash, undo_patch
from app.core.schemas import DetectionConfig, IssueGroup
from app.detection.engine import run_detection
from app.profiling.number_words import words_to_number
from app.profiling.numbers import parse_number
from app.cleaning.actions.trim_whitespace import TrimWhitespace
from app.cleaning.actions.normalize_case import NormalizeCaseVariants
from app.cleaning.actions.merge_similar import MergeSimilarValues
from app.cleaning.actions.fix_invalid_numeric import FixInvalidNumeric
from app.cleaning.actions.handle_outliers import HandleOutliers
from app.rules.evaluator import evaluate_rule
from app.rules.models import ArithmeticRule, CompareRule, RangeRule


def _df(rows, cols):
    df = pd.DataFrame(rows, columns=cols, dtype=str)
    df.index = range(len(df))
    return df


def test_words_to_number():
    assert words_to_number("twenty") == 20
    assert words_to_number("twenty five") == 25
    assert words_to_number("nineteen") == 19


def test_parse_rupee():
    assert parse_number("₹1,200") == 1200


def test_whitespace_jaipur():
    df = _df([[" Jaipur "], ["Jaipur"]], ["City"])
    groups = run_detection(df, DetectionConfig())
    ws = next(g for g in groups if g.subtype == "whitespace")
    assert ws.column == "City"
    act = TrimWhitespace()
    ch = act.build_changes(df, {"collapse_internal": True}, issue=ws)
    assert any(c.after == "Jaipur" and c.before == " Jaipur " for c in ch)
    assert act.risk({}) == "safe"


def test_case_variant_jaipur():
    df = _df([["jaipur"], ["Jaipur"], ["Jaipur"]], ["City"])
    groups = run_detection(df, DetectionConfig())
    g = next(g for g in groups if g.subtype == "case_variant")
    ch = NormalizeCaseVariants().build_changes(df, {"canonical": "most_frequent"}, issue=g)
    assert any(c.after.strip() in {"Jaipur", "jaipur"} for c in ch)


def test_similar_japur_review():
    rows = [["Jaipur"]] * 20 + [["Japur"]]
    df = _df(rows, ["City"])
    groups = run_detection(df, DetectionConfig())
    g = next(g for g in groups if g.subtype == "similar_values")
    ch = MergeSimilarValues().build_changes(df, {}, issue=g)
    assert all(not c.selected for c in ch)
    assert MergeSimilarValues().risk({}) == "review"


def test_age_twenty():
    df = _df([[str(16 + (i % 6))] for i in range(20)] + [["twenty"]], ["Age"])
    groups = run_detection(df, DetectionConfig())
    g = next(g for g in groups if g.type == "invalid_numeric")
    ch = FixInvalidNumeric().build_changes(df, {"mode": "convert_words"}, issue=g)
    assert any(c.after == "20" for c in ch)


def test_range_rule():
    df = _df([["4"], ["8"]], ["Rating"])
    rule = RangeRule(id="r1", name="rating", column="Rating", min=1, max=5)
    res = evaluate_rule(df, rule)
    assert res["violations"] == 1
    assert "8" in list(res["reasons"].values())[0]


def test_outlier_copy():
    vals = [[str(i)] for i in list(range(1, 21))] + [["100000"]]
    df = _df(vals, ["Quantity"])
    groups = run_detection(df, DetectionConfig(outlier_min_values=20))
    g = next(g for g in groups if g.type == "outlier")
    assert "Suspicious, not necessarily wrong" in g.reason
    ch = HandleOutliers().build_changes(df, {"mode": "keep"}, issue=g)
    assert ch == []


def test_dates_mixed_dayfirst():
    df = _df([["25/10/2026"], ["2026-10-25"]], ["Enrollment_Date"])
    groups = run_detection(df, DetectionConfig())
    assert any(g.subtype == "date_mixed" for g in groups)


def test_start_end_rule():
    df = _df([["2025-03-04", "2025-01-02"]], ["Start_Date", "End_Date"])
    rule = CompareRule(
        id="c1",
        name="order",
        left="End_Date",
        op="gte",
        right={"column": "Start_Date"},
        value_type="date",
    )
    res = evaluate_rule(df, rule)
    assert res["violations"] == 1
    assert "End_Date" in list(res["reasons"].values())[0]


def test_arithmetic():
    df = _df([["2", "10", "15"]], ["Quantity", "Unit_Price", "Total_Price"])
    rule = ArithmeticRule(id="a1", name="tot", target="Total_Price", left="Quantity", op="mul", right="Unit_Price")
    res = evaluate_rule(df, rule)
    assert res["violations"] == 1


def test_duplicate_id():
    df = _df([["S1"], ["S1"], ["S2"]], ["Student_ID"])
    groups = run_detection(df, DetectionConfig())
    assert any(g.type == "duplicate_id" for g in groups)


def test_duplicate_rows():
    df = _df([["a", "b"], ["a", "b"], ["c", "d"]], ["X", "Y"])
    groups = run_detection(df, DetectionConfig())
    g = next(g for g in groups if g.type == "duplicate_row")
    from app.cleaning.actions.remove_dups import RemoveDuplicateRows

    assert RemoveDuplicateRows().risk({}) == "destructive"


def test_apply_undo_hash():
    df = _df([[" Jaipur "], ["x"]], ["City"])
    patch = {"cells": [{"rid": 0, "col": "City", "old": " Jaipur ", "new": "Jaipur"}], "deleted_rows": []}
    h0 = state_hash(df)
    df2 = apply_patch(df, patch)
    df3 = undo_patch(df2, patch)
    assert state_hash(df3) == h0
