from __future__ import annotations

import sqlite3
from pathlib import Path

# SQLite file inside the package data directory.
DB_PATH = Path(__file__).resolve().parent / "data" / "clinic.db"


def get_connection() -> sqlite3.Connection:
    """
    Return a SQLite connection with row access by column name.
    Ensures the database directory exists.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    """Create basic tables if they do not exist yet."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()
