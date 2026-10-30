from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pandas as pd
from charset_normalizer import from_bytes

from app.config import settings
from app.errors import AppError

CANDIDATES = [",", ";", "\t", "|"]


def detect_encoding(raw: bytes) -> tuple[str, float]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", 1.0
    if raw.startswith(b"\xff\xfe"):
        return "utf-16", 1.0
    if raw.startswith(b"\xfe\xff"):
        return "utf-16-be", 1.0
    try:
        best = from_bytes(raw).best()
        if best:
            return best.encoding or "utf-8", float(best.percent_coherence or 70) / 100
    except Exception:
        pass
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            raw.decode(enc)
            return enc, 0.6
        except UnicodeDecodeError:
            continue
    return "latin-1", 0.3


def detect_delimiter(text: str) -> tuple[str, float]:
    sample = text[:65536]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(CANDIDATES))
        return dialect.delimiter, 0.9
    except csv.Error:
        pass
    lines = [ln for ln in sample.splitlines() if ln.strip()][:50]
    best, best_score = ",", 0.0
    for d in CANDIDATES:
        counts = [ln.count(d) for ln in lines]
        if not counts:
            continue
        mode = max(set(counts), key=counts.count)
        score = counts.count(mode) / len(counts)
        if mode > 0 and score > best_score:
            best, best_score = d, score
    return best, best_score


def _fix_headers(headers: list[str]) -> tuple[list[str], list[dict]]:
    seen: dict[str, int] = {}
    out: list[str] = []
    notes: list[dict] = []
    for i, h in enumerate(headers):
        name = (h or "").strip() or f"Unnamed: {i}"
        orig = name
        if name in seen:
            seen[name] += 1
            name = f"{orig}.{seen[orig]}"
            notes.append({"from": orig, "to": name, "reason": "duplicate header"})
        else:
            seen[name] = 0
            if not (h or "").strip():
                notes.append({"from": h, "to": name, "reason": "blank header"})
        out.append(name)
    return out, notes


def parse_csv_bytes(
    raw: bytes,
    filename: str,
    delimiter: str | None = None,
    encoding: str | None = None,
    has_header: bool = True,
) -> tuple[pd.DataFrame, dict]:
    if b"\x00" in raw[:4096] and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise AppError("NOT_TEXT", "That file doesn't look like a CSV.", "Export it as CSV from Excel and try again.")
    if not raw.strip():
        raise AppError("EMPTY_FILE", "The file is empty.", "Choose a CSV that has a header and at least one row.")

    enc, enc_conf = (encoding, 1.0) if encoding and encoding.lower() != "auto" else detect_encoding(raw)
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError as e:
        raise AppError("PARSE_FAILED", f"Could not decode as {enc}.", "Try another encoding in parse options.") from e

    delim, delim_conf = (delimiter, 1.0) if delimiter and delimiter != "auto" else detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = list(reader)
    if not rows:
        raise AppError("EMPTY_FILE", "The file is empty.", "Choose a CSV that has a header and at least one row.")

    if has_header:
        headers, header_notes = _fix_headers(rows[0])
        data_rows = rows[1:]
    else:
        width = max((len(r) for r in rows), default=0)
        headers = [f"column_{i+1}" for i in range(width)]
        header_notes = []
        data_rows = rows

    if not data_rows:
        raise AppError("NO_DATA_ROWS", "The file only has a header row.", "Add some data rows and upload again.")

    expected = len(headers)
    malformed: list[dict] = []
    cleaned: list[list[str]] = []
    for i, row in enumerate(data_rows):
        line_no = i + (2 if has_header else 1)
        actual = len(row)
        extra: list[str] = []
        if actual < expected:
            row = row + [""] * (expected - actual)
            malformed.append(
                {
                    "line": line_no,
                    "expected": expected,
                    "actual": actual,
                    "raw_preview": ",".join(row)[:200],
                    "handling": "padded with blanks",
                    "extra_fields": [],
                }
            )
        elif actual > expected:
            extra = row[expected:]
            row = row[:expected]
            malformed.append(
                {
                    "line": line_no,
                    "expected": expected,
                    "actual": actual,
                    "raw_preview": ",".join(row + extra)[:200],
                    "handling": "kept first N fields",
                    "extra_fields": extra,
                }
            )
        # truncate huge cells in preview only; keep data up to max
        row = [c[:32768] if len(c) > 32768 else c for c in row]
        cleaned.append(row)

    if len(cleaned) > settings.MAX_ROWS:
        raise AppError("FILE_TOO_LARGE", f"This file has {len(cleaned)} rows.", f"The limit is {settings.MAX_ROWS} rows.")
    if expected > settings.MAX_COLUMNS:
        raise AppError("FILE_TOO_LARGE", f"This file has {expected} columns.", f"The limit is {settings.MAX_COLUMNS} columns.")

    df = pd.DataFrame(cleaned, columns=headers, dtype=str)
    df.index = range(len(df))
    df.index.name = "rid"
    severity = "ok" if not malformed else "warning"
    report = {
        "filename": filename,
        "encoding": enc,
        "encoding_confidence": enc_conf,
        "delimiter": delim if delim != "\t" else "tab",
        "delimiter_confidence": delim_conf,
        "has_header": has_header,
        "rows": len(df),
        "columns": list(df.columns),
        "header_notes": header_notes,
        "malformed_rows": malformed,
        "severity": severity,
        "message": "Parsed cleanly" if not malformed else f"Parsed with {len(malformed)} warnings",
    }
    return df, report


def save_original(folder: Path, raw: bytes, df: pd.DataFrame, report: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "original.csv").write_bytes(raw)
    df.to_pickle(folder / "original.pkl")
    (folder / "parse_report.json").write_text(json.dumps(report), encoding="utf-8")
