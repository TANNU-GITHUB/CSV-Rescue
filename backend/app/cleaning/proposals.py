from __future__ import annotations

import hashlib

from app.cleaning.registry import BY_ID, for_issue
from app.core.schemas import Proposal


def _scope_hash(rids: list[int]) -> str:
    raw = ",".join(str(r) for r in sorted(rids)[:50])
    return hashlib.sha1(raw.encode()).hexdigest()[:8]


def build_proposals(
    df,
    issues,
    head_seq: int,
    decisions: dict[str, str],
    saved_params: dict[str, dict] | None = None,
) -> list[Proposal]:
    locked = set()
    props: list[Proposal] = []
    saved_params = saved_params or {}
    for issue in issues:
        if issue.status != "open":
            continue
        if issue.column and issue.column in locked:
            continue
        actions = for_issue(issue)
        if not actions:
            continue
        primary = actions[0]
        key = f"{primary.id}:{issue.column or '*'}:{_scope_hash(issue.rids)}"
        params = {p.name: p.default for p in primary.param_schema()}
        params.update(saved_params.get(key, {}))
        changes = primary.build_changes(df, params, issue=issue)
        status = decisions.get(key, "pending")
        risk = primary.risk(params)
        if any(c.kind == "row_delete" for c in changes):
            risk = "destructive"
        warnings = []
        if risk == "destructive":
            warnings.append("This removes rows. You can undo it.")
        if risk == "review":
            warnings.append("Please review — some values are a best guess.")
        n_del = sum(1 for c in changes if c.kind == "row_delete")
        props.append(
            Proposal(
                key=key,
                action=primary.id,
                title=primary.title(issue.column, len(changes) or issue.rid_count),
                explanation=primary.explanation(issue.column, len(changes) or issue.rid_count, params),
                column=issue.column,
                columns=issue.columns,
                issue_keys=[issue.key],
                params=params,
                param_schema=primary.param_schema(),
                alternatives=primary.alternatives(),
                risk=risk,  # type: ignore
                warnings=warnings,
                cells_affected=sum(1 for c in changes if c.kind == "cell_update"),
                rows_affected=len({c.rid for c in changes}),
                rows_deleted=n_del,
                status=status,  # type: ignore
                priority=primary.priority,
                based_on_seq=head_seq,
                changes=changes,
            )
        )
    props.sort(key=lambda p: (p.priority, -p.cells_affected))
    return props


def recompute(df, proposal: Proposal, params: dict) -> Proposal:
    action = BY_ID[proposal.action]
    issue_like = type("I", (), {})()
    issue_like.column = proposal.column
    issue_like.rids = [c.rid for c in proposal.changes] or []
    issue_like.type = ""
    issue_like.subtype = ""
    issue_like.stats = {}
    # keep existing rids from changes; caller should pass issue
    changes = action.build_changes(df, params, issue=proposal)
    # Proposal is not an issue - better path used in API with actual issue
    proposal.params = params
    proposal.changes = changes
    proposal.cells_affected = sum(1 for c in changes if c.kind == "cell_update")
    proposal.rows_affected = len({c.rid for c in changes})
    proposal.rows_deleted = sum(1 for c in changes if c.kind == "row_delete")
    proposal.risk = action.risk(params)  # type: ignore
    return proposal
