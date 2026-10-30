from __future__ import annotations

import csv
import io
import json
import zipfile
from urllib.parse import quote

import pandas as pd
from fastapi.responses import Response, StreamingResponse


def df_to_csv_bytes(df: pd.DataFrame, delimiter: str = ",", encoding: str = "utf-8", line_ending: str = "\n", escape_formulas: bool = False) -> bytes:
    buf = io.StringIO()
    newline = ""  # csv module
    w = csv.writer(buf, delimiter=delimiter if delimiter != "tab" else "\t", quoting=csv.QUOTE_MINIMAL, lineterminator=line_ending)
    w.writerow(list(df.columns))
    for _, row in df.iterrows():
        vals = []
        for v in row.tolist():
            s = "" if v is None else str(v)
            if escape_formulas and s[:1] in "=+-@":
                s = "'" + s
            vals.append(s)
        w.writerow(vals)
    data = buf.getvalue().encode(encoding)
    if encoding == "utf-8-sig" and not data.startswith(b"\xef\xbb\xbf"):
        data = b"\xef\xbb\xbf" + data
    return data


def attachment(content: bytes, filename: str, media: str) -> Response:
    disp = f"attachment; filename*=UTF-8''{quote(filename)}"
    return Response(content=content, media_type=media, headers={"Content-Disposition": disp})


def zip_bundle(files: dict[str, bytes], zip_name: str) -> Response:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return attachment(buf.getvalue(), zip_name, "application/zip")
