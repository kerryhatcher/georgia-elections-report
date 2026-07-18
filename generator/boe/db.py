"""SQLite connection + schema for the board-of-elections database.

The database file lives at the repository root (``database.db``), gitignored,
so every contributor gets a local working copy. Override the path with the
``BOE_DB_PATH`` environment variable (handy for tests).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# boe/db.py → generator/boe/  → generator/  → repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "database.db"

SCHEMA = """
-- Counties: one row per Georgia county.
CREATE TABLE IF NOT EXISTS counties (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    slug       TEXT NOT NULL UNIQUE,
    fips       TEXT,
    seat       TEXT,
    population INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Boards: one per county (1:1), the body that runs elections there.
CREATE TABLE IF NOT EXISTS boards (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    county_id             INTEGER NOT NULL REFERENCES counties(id) ON DELETE CASCADE,
    name                  TEXT NOT NULL,
    organization          TEXT,
    meeting_schedule      TEXT,
    meeting_location       TEXT,
    selection_method      TEXT CHECK (selection_method IN ('appointed','elected','mixed')),
    selection_description TEXT,
    authority             TEXT,
    term_length           TEXT,
    notes                 TEXT,
    created_at            TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at            TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (county_id)
);

-- Members: people who sit on a board.
CREATE TABLE IF NOT EXISTS members (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id               INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    name                   TEXT NOT NULL,
    role                   TEXT,
    party                  TEXT,
    is_elected             INTEGER NOT NULL DEFAULT 0,
    appointed_by           TEXT,
    appointment_method     TEXT,
    appointment_authority  TEXT,
    term_start             TEXT,
    term_end               TEXT,
    notes                  TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at             TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Full-text search over counties, boards, and members.
CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(
    entity_type UNINDEXED,
    entity_id   UNINDEXED,
    title,
    body,
    tokenize = 'porter unicode61'
);

-- Persisted networkx graph: nodes and edges, attrs as JSON.
CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id   TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    name      TEXT,
    attrs     TEXT
);
CREATE TABLE IF NOT EXISTS graph_edges (
    src      TEXT NOT NULL,
    tgt      TEXT NOT NULL,
    relation TEXT NOT NULL,
    attrs    TEXT,
    PRIMARY KEY (src, tgt, relation)
);

CREATE INDEX IF NOT EXISTS idx_members_board ON members(board_id);
"""


def db_path() -> Path:
    """Resolved database path (env-overridable)."""
    return Path(os.environ.get("BOE_DB_PATH") or DEFAULT_DB_PATH)


def connect() -> sqlite3.Connection:
    """Open a connection with FK enforcement + WAL for concurrent reads."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    """Create all tables if missing. Idempotent."""
    db_path().parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()