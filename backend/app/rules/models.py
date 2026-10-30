from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class ColumnRef(BaseModel):
    column: str


class ValueRef(BaseModel):
    value: str


class BaseRule(BaseModel):
    id: str
    name: str
    severity: Literal["error", "warning", "info"] = "error"
    enabled: bool = True
    origin: Literal["user", "suggested", "ai"] = "user"
    description: str | None = None


class CompareRule(BaseRule):
    type: Literal["compare"] = "compare"
    left: str
    op: Literal["eq", "ne", "lt", "lte", "gt", "gte", "contains", "not_contains", "starts_with", "ends_with"]
    right: dict
    value_type: Literal["number", "date", "text"] = "text"
    skip_blank: bool = True


class RangeRule(BaseRule):
    type: Literal["range"] = "range"
    column: str
    min: float | None = None
    max: float | None = None
    inclusive: bool = True


class ArithmeticRule(BaseRule):
    type: Literal["arithmetic"] = "arithmetic"
    target: str
    left: str
    op: Literal["add", "sub", "mul", "div"]
    right: str | float
    tolerance_abs: float = 0.01
    tolerance_rel: float = 0.0


class FormatRule(BaseRule):
    type: Literal["format"] = "format"
    column: str
    preset: Literal["email", "phone_in", "phone_intl", "url", "pincode_in", "custom"] = "email"
    pattern: str | None = None


class UniqueRule(BaseRule):
    type: Literal["unique"] = "unique"
    columns: list[str]


class NotNullRule(BaseRule):
    type: Literal["not_null"] = "not_null"
    columns: list[str]


class AllowedValuesRule(BaseRule):
    type: Literal["allowed_values"] = "allowed_values"
    column: str
    values: list[str]
    case_sensitive: bool = False


Rule = Annotated[
    Union[CompareRule, RangeRule, ArithmeticRule, FormatRule, UniqueRule, NotNullRule, AllowedValuesRule],
    Field(discriminator="type"),
]


def parse_rule(data: dict) -> BaseModel:
    t = data.get("type")
    mapping = {
        "compare": CompareRule,
        "range": RangeRule,
        "arithmetic": ArithmeticRule,
        "format": FormatRule,
        "unique": UniqueRule,
        "not_null": NotNullRule,
        "allowed_values": AllowedValuesRule,
    }
    cls = mapping.get(t)
    if not cls:
        raise ValueError("Unknown rule type")
    return cls.model_validate(data)


def summarize(rule: BaseModel) -> str:
    t = rule.type
    if t == "range":
        return f"{rule.column} should be between {rule.min} and {rule.max}"
    if t == "compare":
        right = rule.right.get("column") or rule.right.get("value")
        return f"{rule.left} should be {rule.op} {right}"
    if t == "arithmetic":
        return f"{rule.target} should equal {rule.left} {rule.op} {rule.right} (±{rule.tolerance_abs})"
    if t == "format":
        return f"{rule.column} should look like a valid {rule.preset}"
    if t == "unique":
        return f"{', '.join(rule.columns)} should be unique"
    if t == "not_null":
        return f"{', '.join(rule.columns)} is required"
    if t == "allowed_values":
        return f"{rule.column} should be one of {', '.join(rule.values[:6])}"
    return rule.name
