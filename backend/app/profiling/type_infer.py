from __future__ import annotations

import re

from app.core.schemas import DetectionConfig
from app.profiling.dates import EMAIL_RE, looks_like_date
from app.profiling.numbers import looks_decimal, looks_integer

BOOL_TOKENS = {"true", "false", "yes", "no", "y", "n", "t", "f", "1", "0"}
BOOL_NAME = re.compile(r"(is_|has_|flag|active)", re.I)
UNIQUE_NAME = None  # compiled per config


def _nonblank(series) -> list[str]:
    out = []
    for v in series:
        s = str(v)
        if s.strip() != "":
            out.append(s)
    return out


def infer_column(name: str, values: list[str], config: DetectionConfig) -> tuple[str, float, dict]:
    n = len(values)
    extra: dict = {}
    if n == 0:
        return "text", 0.0, extra
    trimmed = [v.strip() for v in values]
    tokens = set(t.lower() for t in trimmed)
    # boolean
    if tokens.issubset(BOOL_TOKENS) and len(tokens) >= 2:
        if tokens <= {"0", "1"} and not BOOL_NAME.search(name):
            pass
        else:
            return "boolean", 1.0, extra
    int_ok = sum(1 for v in trimmed if looks_integer(v))
    if int_ok / n >= config.type_confidence:
        return "integer", int_ok / n, extra
    dec_ok = sum(1 for v in trimmed if looks_decimal(v) or looks_integer(v))
    if dec_ok / n >= config.type_confidence:
        return "decimal", dec_ok / n, extra
    date_ok = sum(1 for v in trimmed if looks_like_date(v))
    if date_ok / n >= config.type_confidence:
        return "date", date_ok / n, extra
    email_ok = sum(1 for v in trimmed if EMAIL_RE.match(v))
    if email_ok / n >= config.type_confidence:
        return "email", email_ok / n, extra
    distinct = len(set(t.casefold() for t in trimmed))
    avg_len = sum(len(t) for t in trimmed) / n
    unique_re = re.compile(config.unique_name_patterns, re.I)
    if unique_re.search(name) and distinct / n >= config.unique_min_distinct_ratio:
        return "id", distinct / n, extra
    if distinct <= min(50, max(2, int(0.05 * n))) and avg_len < 40:
        return "category", 1.0, extra
    return "text", 1.0, extra
