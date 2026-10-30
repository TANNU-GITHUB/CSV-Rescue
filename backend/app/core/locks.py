from __future__ import annotations

import threading

_locks: dict[str, threading.RLock] = {}
_guard = threading.Lock()


def session_lock(session_id: str) -> threading.RLock:
    with _guard:
        if session_id not in _locks:
            _locks[session_id] = threading.RLock()
        return _locks[session_id]
