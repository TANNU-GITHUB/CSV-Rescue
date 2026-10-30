from __future__ import annotations

import re
from datetime import datetime

# family, regex, strptime
PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("ymd-dash", re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    ("ymd-slash", re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),
    ("dmy-slash", re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"), "%d/%m/%Y"),
    ("mdy-slash", re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"), "%m/%d/%Y"),
    ("dmy-dash", re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"), "%d-%m-%Y"),
    ("mdy-dash", re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"), "%m-%d-%Y"),
    ("dmy-dot", re.compile(r"^\d{1,2}\.\d{1,2}\.\d{4}$"), "%d.%m.%Y"),
    ("d-mon-yyyy", re.compile(r"^\d{1,2} [A-Za-z]{3} \d{4}$"), "%d %b %Y"),
    ("dd-month-yyyy", re.compile(r"^\d{1,2} [A-Za-z]+ \d{4}$"), "%d %B %Y"),
    ("mon-d-yyyy", re.compile(r"^[A-Za-z]{3} \d{1,2}, \d{4}$"), "%b %d, %Y"),
    ("month-d-yyyy", re.compile(r"^[A-Za-z]+ \d{1,2}, \d{4}$"), "%B %d, %Y"),
    ("iso-dt", re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:?\d{2})?$"), "%Y-%m-%dT%H:%M"),
]

AMBIGUOUS_FAMILIES = {"dmy-slash", "mdy-slash", "dmy-dash", "mdy-dash"}


def try_parse(value: str, fmt: str) -> datetime | None:
    try:
        if fmt.startswith("%Y-%m-%dT"):
            core = value[:16]
            return datetime.strptime(core, "%Y-%m-%dT%H:%M")
        return datetime.strptime(value.strip(), fmt)
    except ValueError:
        return None


def classify_date(value: str, dayfirst: bool) -> tuple[str | None, str | None, datetime | None, bool, bool]:
    """Return family, format, dt, ambiguous, has_time."""
    v = value.strip()
    has_time = "T" in v and re.match(r"^\d{4}-\d{2}-\d{2}T", v) is not None
    two_digit_year = bool(re.search(r"[/\-.]\d{2}$", v)) and not re.search(r"\d{4}", v)
    if two_digit_year:
        return None, None, None, True, False

    # named months first
    for family, regex, fmt in PATTERNS:
        if family in {"dmy-slash", "mdy-slash", "dmy-dash", "mdy-dash"}:
            continue
        if regex.match(v):
            dt = try_parse(v, fmt)
            if dt:
                return family, fmt, dt, False, has_time

    m = re.match(r"^(\d{1,2})([/\-.])(\d{1,2})\2(\d{4})$", v)
    if m:
        a, sep, b, year = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
        ambiguous = a <= 12 and b <= 12
        if a > 12 and b > 12:
            return None, None, None, False, False
        use_dayfirst = dayfirst
        if a > 12:
            use_dayfirst = True
        elif b > 12:
            use_dayfirst = False
        if use_dayfirst:
            family = {"/": "dmy-slash", "-": "dmy-dash", ".": "dmy-dot"}[sep]
            fmt = {"/": "%d/%m/%Y", "-": "%d-%m-%Y", ".": "%d.%m.%Y"}[sep]
        else:
            family = {"/": "mdy-slash", "-": "mdy-dash", ".": "dmy-dot"}[sep]
            fmt = {"/": "%m/%d/%Y", "-": "%m-%d-%Y", ".": "%d.%m.%Y"}[sep]
        dt = try_parse(v, fmt)
        return family, fmt, dt, ambiguous, False
    return None, None, None, False, has_time


def looks_like_date(value: str) -> bool:
    family, _, dt, _, _ = classify_date(value, True)
    return dt is not None or family is not None


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
