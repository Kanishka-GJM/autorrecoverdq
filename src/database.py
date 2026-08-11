"""
database.py

Handles everything related to the SQLite database:
- Connecting to error_logs.db
- Creating the error_logs table if it does not already exist

Keeping this logic in one place means the rest of the code never
has to write raw SQL for setup.
"""

import sqlite3
from pathlib import Path

# Path to the database file (lives inside logs/)
DB_PATH = Path(__file__).resolve().parent.parent / "logs" / "error_logs.db"


def get_connection() -> sqlite3.Connection:
    """
    Open (and if needed create) a connection to the SQLite database.
    Ensures the logs/ folder exists first.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database() -> None:
    """
    Create the error_logs table if it doesn't already exist.
    This is safe to call every run.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            row_number INTEGER,
            column_name TEXT,
            error_type TEXT NOT NULL,
            original_value TEXT,
            pipeline_stage TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
