from __future__ import annotations

from app.core.session_store import get_working_set, load_row
from app.db import get_db


def session_id_dep(session_id: str) -> str:
    load_row(session_id)
    return session_id
