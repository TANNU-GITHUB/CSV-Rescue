from __future__ import annotations

import re

_ONES = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def words_to_number(text: str) -> int | None:
    raw = text.strip().lower().replace("-", " ")
    raw = re.sub(r"\band\b", " ", raw)
    parts = [p for p in raw.split() if p]
    if not parts:
        return None
    total = 0
    current = 0
    for p in parts:
        if p in _ONES:
            current += _ONES[p]
        elif p in _TENS:
            current += _TENS[p]
        elif p == "hundred":
            current = (current or 1) * 100
        elif p == "thousand":
            total += (current or 1) * 1000
            current = 0
        else:
            return None
        if total + current > 999_999:
            return None
    return total + current
