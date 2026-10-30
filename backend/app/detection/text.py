from __future__ import annotations

import re

import pandas as pd
from rapidfuzz import fuzz, process

from app.core.schemas import DetectionConfig, Evidence, IssueGroup


def _norm(v: str) -> str:
    return re.sub(r"\s+", " ", v.strip()).casefold()


def detect_text(df: pd.DataFrame, metas: list[dict], config: DetectionConfig) -> list[IssueGroup]:
    groups: list[IssueGroup] = []
    meta_by = {m["name"]: m for m in metas}
    for col in df.columns:
        m = meta_by.get(col, {})
        et = m.get("effective_type", "text")
        series = df[col].astype(str)
        values = series.tolist()
        rids = [int(i) for i in df.index.tolist()]
        # whitespace always
        ws_rids = []
        for rid, v in zip(rids, values):
            if v == "":
                continue
            if v != v.strip() or "  " in v or "\u00a0" in v or "\u200b" in v:
                ws_rids.append(rid)
        if ws_rids and et not in {"email"}:
            ev = [Evidence(rid=r, column=col, value=series.loc[r], note="whitespace") for r in ws_rids[:5]]
            groups.append(
                IssueGroup(
                    key=f"inconsistent_text:whitespace:{col}",
                    type="inconsistent_text",
                    subtype="whitespace",
                    column=col,
                    columns=[col],
                    severity="info",
                    rids=ws_rids,
                    cells=len(ws_rids),
                    reason="Some values have extra spaces or hidden characters.",
                    evidence=ev,
                    suggested_next_step="Trim whitespace (safe formatting)",
                    rid_count=len(ws_rids),
                )
            )
        if et in {"email", "id", "date", "integer", "decimal"}:
            continue
        nonblank = [(rid, v) for rid, v in zip(rids, values) if v.strip()]
        if not nonblank:
            continue
        avg_len = sum(len(v) for _, v in nonblank) / len(nonblank)
        distinct_ratio = len({_norm(v) for _, v in nonblank}) / len(nonblank)
        skip_similar = avg_len > 40 and distinct_ratio > 0.5

        buckets: dict[str, dict[str, list[int]]] = {}
        for rid, v in nonblank:
            key = _norm(v)
            buckets.setdefault(key, {}).setdefault(v, []).append(rid)
        case_rids: list[int] = []
        case_ev: list[Evidence] = []
        for forms in buckets.values():
            if len(forms) >= 2:
                for raw, ids in forms.items():
                    case_rids.extend(ids)
                    if len(case_ev) < 5:
                        case_ev.append(Evidence(rid=ids[0], column=col, value=raw, note="case variant"))
        if case_rids:
            groups.append(
                IssueGroup(
                    key=f"inconsistent_text:case_variant:{col}",
                    type="inconsistent_text",
                    subtype="case_variant",
                    column=col,
                    columns=[col],
                    severity="warning",
                    rids=sorted(set(case_rids)),
                    cells=len(set(case_rids)),
                    reason="The same word is written with different capitalisation.",
                    evidence=case_ev,
                    suggested_next_step="Standardise to the most common spelling",
                    rid_count=len(set(case_rids)),
                )
            )

        if skip_similar:
            continue
        norms = sorted({_norm(v) for _, v in nonblank if _norm(v)})
        if 2 <= len(norms) <= config.similar_max_distinct:
            parent = {x: x for x in norms}

            def find(x: str) -> str:
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            counts = {}
            for _, v in nonblank:
                counts[_norm(v)] = counts.get(_norm(v), 0) + 1
            n_nb = len(nonblank)
            matrix = process.cdist(norms, norms, scorer=fuzz.ratio)
            for i, a in enumerate(norms):
                for j in range(i + 1, len(norms)):
                    b = norms[j]
                    score = float(matrix[i][j])
                    if score < config.similar_threshold:
                        continue
                    if re.sub(r"\d", "", a) != re.sub(r"\d", "", b) and re.search(r"\d", a) and re.search(r"\d", b):
                        continue
                    if min(len(a), len(b)) < 4:
                        continue
                    ta, tb = set(a.split()), set(b.split())
                    if ta.symmetric_difference(tb) and all(len(t) <= 2 for t in ta.symmetric_difference(tb)):
                        continue
                    if counts[a] / n_nb >= 0.2 and counts[b] / n_nb >= 0.2:
                        continue
                    pa, pb = find(a), find(b)
                    if pa != pb:
                        parent[pb] = pa
            clusters: dict[str, list[str]] = {}
            for x in norms:
                clusters.setdefault(find(x), []).append(x)
            sim_rids: list[int] = []
            ev: list[Evidence] = []
            stats_pairs = []
            for members in clusters.values():
                if len(members) < 2 or len(members) > 6:
                    continue
                # skip pure case variants already handled
                if len({m.casefold() for m in members}) == 1:
                    continue
                for rid, v in nonblank:
                    if _norm(v) in members:
                        sim_rids.append(rid)
                        if len(ev) < 5:
                            ev.append(Evidence(rid=rid, column=col, value=v, note="similar"))
                stats_pairs.append([(m, counts[m], None) for m in members])
            if sim_rids:
                groups.append(
                    IssueGroup(
                        key=f"inconsistent_text:similar_values:{col}",
                        type="inconsistent_text",
                        subtype="similar_values",
                        column=col,
                        columns=[col],
                        severity="info",
                        rids=sorted(set(sim_rids)),
                        cells=len(set(sim_rids)),
                        reason="Some values look like possible spelling variations of each other.",
                        evidence=ev,
                        suggested_next_step="Review each cluster — we will not auto-merge them",
                        stats={"clusters": stats_pairs},
                        rid_count=len(set(sim_rids)),
                    )
                )
    return groups
