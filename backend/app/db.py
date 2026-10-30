from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT, updated_at TEXT, expires_at TEXT,
  stage TEXT NOT NULL DEFAULT 'uploaded',
  head_seq INTEGER NOT NULL DEFAULT 0,
  verified_seq INTEGER,
  verified_at TEXT,
  settings_json TEXT NOT NULL,
  parse_report_json TEXT NOT NULL,
  n_rows_original INTEGER, n_cols INTEGER
);
CREATE TABLE IF NOT EXISTS operations (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, seq INTEGER NOT NULL,
  batch_id TEXT, kind TEXT NOT NULL,
  title TEXT NOT NULL, params_json TEXT NOT NULL,
  status TEXT NOT NULL,
  proposal_id TEXT, created_at TEXT, undone_at TEXT,
  affected_cells INTEGER, affected_rows INTEGER, rows_deleted INTEGER,
  patch_path TEXT NOT NULL,
  state_hash_after TEXT,
  UNIQUE(session_id, seq)
);
CREATE TABLE IF NOT EXISTS rules (
  id TEXT PRIMARY KEY, session_id TEXT, name TEXT, enabled INTEGER, json TEXT, created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
  session_id TEXT, proposal_key TEXT, status TEXT, reason TEXT, updated_at TEXT,
  PRIMARY KEY(session_id, proposal_key)
);
CREATE TABLE IF NOT EXISTS proposal_settings (
  session_id TEXT NOT NULL, proposal_key TEXT NOT NULL, params_json TEXT NOT NULL,
  PRIMARY KEY(session_id, proposal_key)
);
CREATE TABLE IF NOT EXISTS dismissals (
  session_id TEXT, issue_key TEXT, reason TEXT, rids_json TEXT NOT NULL, created_at TEXT,
  PRIMARY KEY(session_id, issue_key)
);
CREATE TABLE IF NOT EXISTS ai_cache (
  key TEXT PRIMARY KEY, response_json TEXT, source TEXT, created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_ops_session ON operations(session_id, seq);
"""


def db_path() -> Path:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return settings.DATA_DIR / "csvrescue.db"


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(db_path(), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


_con: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    global _con
    if _con is None:
        _con = connect()
        _con.executescript(SCHEMA)
        _con.commit()
    return _con


def init_db() -> None:
    get_db()
