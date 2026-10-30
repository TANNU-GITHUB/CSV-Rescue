from __future__ import annotations

import re

CURRENCY = "₹$€£"
THOUSANDS = re.compile(r"^\d{1,3}(,\d{2,3})+$")
INT_RE = re.compile(r"^[+-]?\d+$")
DEC_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")


def clean_numeric_token(value: str) -> tuple[str, dict]:
    flags: dict = {"currency": False, "percent": False, "parens": False, "thousands": False}
    v = value.strip()
    if v.startswith("(") and v.endswith(")"):
        flags["parens"] = True
        v = "-" + v[1:-1]
    if any(c in v for c in CURRENCY):
        flags["currency"] = True
        for c in CURRENCY:
            v = v.replace(c, "")
        v = v.strip()
    if v.endswith("%"):
        flags["percent"] = True
        v = v[:-1].strip()
    compact = v.replace(",", "")
    if "," in v and THOUSANDS.match(v.lstrip("+-")):
        flags["thousands"] = True
        v = compact
    else:
        v = compact if flags["currency"] or flags["percent"] else v.replace(",", "") if "," in v else v
        if "," in value:
            flags["thousands"] = True
    return v.strip(), flags


def parse_number(value: str) -> float | None:
    token, _ = clean_numeric_token(value)
    if INT_RE.match(token) or DEC_RE.match(token):
        try:
            return float(token)
        except ValueError:
            return None
    return None


def looks_integer(value: str) -> bool:
    token, _ = clean_numeric_token(value)
    return bool(INT_RE.match(token))


def looks_decimal(value: str) -> bool:
    token, _ = clean_numeric_token(value)
    return bool(DEC_RE.match(token))
