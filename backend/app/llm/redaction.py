from __future__ import annotations

import re

EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}")


def redact(text: str) -> str:
    text = EMAIL.sub("<email>", text)
    text = PHONE.sub("<phone>", text)
    return text


def redact_list(values: list[str]) -> list[str]:
    return [redact(v) for v in values[:20]]
