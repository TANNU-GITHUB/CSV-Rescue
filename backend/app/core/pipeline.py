from __future__ import annotations

import json

from app.cleaning.proposals import build_proposals
from app.core.session_store import get_working_set, load_row
from app.db import get_db
from app.detection.engine import run_detection
from app.profiling.profiler import profile_dataframe
from app.rules.evaluator import evaluate_rule
from app.rules.models import parse_rule
from app.verification.scoring import quality_scores


def load_rules(sid: str) -> list:
    db = get_db()
    rows = db.execute("SELECT json FROM rules WHERE session_id=?", (sid,)).fetchall()
    return [parse_rule(json.loads(r["json"])) for r in rows]


def eval_rules(df, rules, dayfirst=True) -> list[dict]:
    return [evaluate_rule(df, r, dayfirst) for r in rules]


def dismiss_map(sid: str) -> dict[str, set[int]]:
    db = get_db()
    rows = db.execute("SELECT issue_key, rids_json FROM dismissals WHERE session_id=?", (sid,)).fetchall()
    return {r["issue_key"]: set(json.loads(r["rids_json"])) for r in rows}


def decisions_map(sid: str) -> dict[str, str]:
    db = get_db()
    rows = db.execute("SELECT proposal_key, status FROM decisions WHERE session_id=?", (sid,)).fetchall()
    return {r["proposal_key"]: r["status"] for r in rows}


def detect_current(sid: str):
    ws = get_working_set(sid)
    key = f"det:{ws.head_seq}"
    if key in ws.cache:
        return ws.cache[key]
    rules = eval_rules(ws.df, load_rules(sid), ws.config.dayfirst_default)
    groups = run_detection(ws.df, ws.config, rules, dismiss_map(sid))
    ws.cache[key] = (groups, rules)
    return groups, rules


def detect_original(sid: str):
    ws = get_working_set(sid)
    key = "det_orig"
    if key in ws.cache:
        return ws.cache[key]
    rules = eval_rules(ws.original, load_rules(sid), ws.config.dayfirst_default)
    groups = run_detection(ws.original, ws.config, rules, {})
    ws.cache[key] = (groups, rules)
    return groups, rules


def proposals_for(sid: str):
    ws = get_working_set(sid)
    groups, _ = detect_current(sid)
    db = get_db()
    rows = db.execute(
        "SELECT proposal_key, params_json FROM proposal_settings WHERE session_id=?",
        (sid,),
    ).fetchall()
    params = {r["proposal_key"]: json.loads(r["params_json"]) for r in rows}
    return build_proposals(ws.df, groups, ws.head_seq, decisions_map(sid), params)


def profile_for(sid: str, view: str = "current"):
    ws = get_working_set(sid)
    df = ws.original if view == "original" else ws.df
    return profile_dataframe(df, ws.config)


def dashboard_payload(sid: str) -> dict:
    ws = get_working_set(sid)
    row = load_row(sid)
    groups, _ = detect_current(sid)
    orig_groups, _ = detect_original(sid)
    open_g = [g for g in groups if g.status == "open"]
    scores = quality_scores(len(ws.df), len(ws.df.columns), open_g)
    orig_scores = quality_scores(len(ws.original), len(ws.original.columns), orig_groups)
    db = get_db()
    ops = db.execute(
        "SELECT id, title, kind, status, created_at, affected_cells, rows_deleted FROM operations WHERE session_id=? ORDER BY seq DESC LIMIT 8",
        (sid,),
    ).fetchall()
    props = proposals_for(sid)
    pending = [p for p in props if p.status == "pending"]
    safe = [p for p in pending if p.risk == "safe"]
    type_counts = {}
    for g in orig_groups:
        slot = type_counts.setdefault(g.type, {"type": g.type, "detected": 0, "remaining": 0, "resolved": 0})
        slot["detected"] += g.rid_count
    for g in open_g:
        type_counts.setdefault(g.type, {"type": g.type, "detected": 0, "remaining": 0, "resolved": 0})
        type_counts[g.type]["remaining"] += g.rid_count
    for t, slot in type_counts.items():
        slot["resolved"] = max(slot["detected"] - slot["remaining"], 0)
    col_counts: dict[str, int] = {}
    for g in open_g:
        if g.column:
            col_counts[g.column] = col_counts.get(g.column, 0) + g.rid_count
    applied = db.execute(
        "SELECT COUNT(*) n FROM operations WHERE session_id=? AND status='applied'", (sid,)
    ).fetchone()["n"]
    undone = db.execute(
        "SELECT COUNT(*) n FROM operations WHERE session_id=? AND status='undone'", (sid,)
    ).fetchone()["n"]
    rejected = db.execute(
        "SELECT COUNT(*) n FROM decisions WHERE session_id=? AND status='rejected'", (sid,)
    ).fetchone()["n"]
    stage = row["stage"]
    n_open = len(open_g)
    if n_open == 0 and applied:
        headline, sub, cta, route = "Ready to export", "Verify once more, then download a clean file.", "Export now", "/reports"
        action = None
    elif pending:
        headline, sub, cta, route = "Review suggestions", f"{len(pending)} cleaning ideas are waiting.", "Open Cleaning Studio", "/studio"
        action = None
    else:
        headline, sub, cta, route = "Start with a CSV", "Drop in a messy file and we'll find what needs fixing.", "Upload a CSV", "/datasets"
        action = "upload"
    if stage in {"verified"}:
        headline, sub, cta, route = "Ready to export", "Your last verification is on this version.", "Export now", "/reports"
    return {
        "dataset": {
            "filename": row["filename"],
            "rows": len(ws.df),
            "rowsOriginal": len(ws.original),
            "columns": len(ws.df.columns),
        },
        "stats": {
            "rows": len(ws.df),
            "openIssues": n_open,
            "qualityScore": scores["quality_score"],
            "qualityDelta": round(scores["quality_score"] - orig_scores["quality_score"], 1),
            "changesApplied": applied,
            "changesUndone": undone,
            "proposalsRejected": rejected,
            "resolvedIssues": max(len(orig_groups) - n_open, 0),
        },
        "issuesByType": list(type_counts.values()),
        "issuesByColumn": [{"column": k, "open": v} for k, v in sorted(col_counts.items(), key=lambda x: -x[1])],
        "recentOps": [dict(o) for o in ops[:3]],
        "quickWins": {
            "count": len(safe),
            "cells": sum(p.cells_affected for p in safe),
            "proposals": [{"key": p.key, "title": p.title, "cells": p.cells_affected} for p in safe[:8]],
        },
        "nextStep": {
            "stage": stage,
            "headline": headline,
            "subline": sub,
            "cta": {"label": cta, "route": route, "action": action},
        },
    }
