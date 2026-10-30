from __future__ import annotations

import secrets


def new_id(nbytes: int = 16) -> str:
    return secrets.token_urlsafe(nbytes)
