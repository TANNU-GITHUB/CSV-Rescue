from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

IssueType = Literal[
    "missing_value",
    "duplicate_row",
    "inconsistent_text",
    "inconsistent_format",
    "invalid_numeric",
    "invalid_value",
    "outlier",
    "duplicate_id",
]
Severity = Literal["error", "warning", "info"]
Risk = Literal["safe", "review", "destructive"]
Stage = Literal["uploaded", "profiled", "reviewing", "reviewed", "verified", "exported"]


class Evidence(BaseModel):
    rid: int
    column: str
    value: str
    note: str = ""


class IssueGroup(BaseModel):
    key: str
    type: str
    subtype: str
    column: str | None = None
    columns: list[str] = Field(default_factory=list)
    severity: Severity = "warning"
    rids: list[int] = Field(default_factory=list)
    cells: int = 0
    reason: str
    evidence: list[Evidence] = Field(default_factory=list)
    suggested_next_step: str = ""
    stats: dict[str, Any] = Field(default_factory=dict)
    status: Literal["open", "dismissed", "resolved"] = "open"
    rid_count: int = 0


class DetectionConfig(BaseModel):
    missing_tokens: list[str] = Field(
        default_factory=lambda: [
            "na",
            "n/a",
            "nan",
            "null",
            "none",
            "nil",
            "-",
            "--",
            "?",
            "missing",
            "#n/a",
        ]
    )
    type_confidence: float = 0.90
    dayfirst_default: bool = True
    date_output_format: str = "%Y-%m-%d"
    similar_threshold: int = 85
    similar_max_distinct: int = 200
    outlier_min_values: int = 20
    outlier_sensitivity: Literal["relaxed", "standard", "strict"] = "standard"
    unique_name_patterns: str = (
        r"(^|_|\b)(id|uuid|guid|sku|code|email|roll_?no|reg(istration)?_?(no|number)|ref(erence)?)($|_|\b)"
    )
    unique_min_distinct_ratio: float = 0.90
    duplicate_ignore_columns: list[str] = Field(default_factory=list)
    locked_columns: list[str] = Field(default_factory=list)
    unique_columns: list[str] = Field(default_factory=list)
    type_overrides: dict[str, str] = Field(default_factory=dict)
    llm_mode: Literal["auto", "ollama_only", "off"] = "auto"
    redact_pii: bool = True


class ColumnMeta(BaseModel):
    name: str
    inferred_type: str
    type_confidence: float
    override_type: str | None = None
    effective_type: str
    date_formats: list[dict] | None = None
    dayfirst_resolved: bool | None = None
    is_unique_declared: bool = False
    unique_auto: bool = False


class Change(BaseModel):
    id: str
    kind: Literal["cell_update", "row_delete"]
    rid: int
    column: str | None = None
    before: str | None = None
    after: str | None = None
    reason: str
    confidence: float = 1.0
    selected: bool = True
    override: str | None = None


class ParamSpec(BaseModel):
    name: str
    label: str
    kind: Literal["select", "number", "text", "toggle"]
    options: list[str] = Field(default_factory=list)
    default: Any = None


class AlternativeAction(BaseModel):
    action: str
    title: str
    params: dict[str, Any] = Field(default_factory=dict)


class Proposal(BaseModel):
    key: str
    action: str
    title: str
    explanation: str
    column: str | None = None
    columns: list[str] = Field(default_factory=list)
    issue_keys: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    param_schema: list[ParamSpec] = Field(default_factory=list)
    alternatives: list[AlternativeAction] = Field(default_factory=list)
    risk: Risk = "safe"
    warnings: list[str] = Field(default_factory=list)
    cells_affected: int = 0
    rows_affected: int = 0
    rows_deleted: int = 0
    status: Literal["pending", "applied", "rejected", "skipped", "partial"] = "pending"
    priority: int = 50
    based_on_seq: int = 0
    changes: list[Change] = Field(default_factory=list)


class SessionMeta(BaseModel):
    id: str
    filename: str
    stage: str
    head_seq: int
    verified_seq: int | None = None
    verified_at: str | None = None
    n_rows: int = 0
    n_rows_original: int = 0
    n_cols: int = 0
    created_at: str | None = None
    updated_at: str | None = None
