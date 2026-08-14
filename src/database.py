"""
database.py

Handles everything related to the SQLite database:
- Connecting to error_logs.db
- Creating the error_logs table if it does not already exist
- Creating the recovery_logs table (Phase 2)
- Creating the error_patterns table (Phase 3)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Path to the database file (lives inside logs/)
DB_PATH = Path(__file__).resolve().parent.parent / "logs" / "error_logs.db"

def get_connection() -> sqlite3.Connection:
    """Open (and if needed create) a connection to the SQLite database.
    Ensures the logs/ folder exists first.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_database() -> None:
    """Create the error_logs, recovery_logs, and error_patterns tables if they don't already exist.
    This is safe to call every run.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # error_logs table (Phase 1)
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

    # recovery_logs table (Phase 2)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            row_number INTEGER,
            column_name TEXT,
            error_type TEXT NOT NULL,
            correction_applied TEXT NOT NULL,
            original_value TEXT,
            corrected_value TEXT,
            recovery_status TEXT NOT NULL
        )
    """)

    # error_patterns table (Phase 3)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_name TEXT UNIQUE,
            error_type TEXT NOT NULL,
            column_name TEXT,
            correction_rule TEXT,
            frequency INTEGER DEFAULT 1,
            first_seen TEXT,
            last_seen TEXT,
            confidence REAL DEFAULT 1.0,
            auto_fix_enabled INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()

# --- Phase 3 Pattern Library Helpers ---

def get_pattern(pattern_name: str) -> Optional[Dict]:
    """Retrieve an existing pattern by its name."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM error_patterns WHERE pattern_name=?", (pattern_name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "pattern_name": row[1],
            "error_type": row[2],
            "column_name": row[3],
            "correction_rule": row[4],
            "frequency": row[5],
            "first_seen": row[6],
            "last_seen": row[7],
            "confidence": row[8],
            "auto_fix_enabled": row[9]
        }
    return None

def insert_pattern(pattern_name: str, error_type: str, column_name: str, correction_rule: str) -> None:
    """Create a new error pattern entry."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO error_patterns 
        (pattern_name, error_type, column_name, correction_rule, frequency, first_seen, last_seen)
        VALUES (?, ?, ?, ?, 1, ?, ?)
    """, (pattern_name, error_type, column_name, correction_rule, now, now))
    conn.commit()
    conn.close()

def update_pattern_frequency(pattern_name: str) -> None:
    """Increment the frequency of a known pattern and update its last_seen timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE error_patterns 
        SET frequency = frequency + 1, last_seen = ?
        WHERE pattern_name = ?
    """, (now, pattern_name))
    conn.commit()
    conn.close()

def list_patterns() -> List[Dict]:
    """Retrieve all learned patterns, ordered by frequency."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pattern_name, frequency, correction_rule FROM error_patterns ORDER BY frequency DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"pattern_name": r[0], "frequency": r[1], "correction_rule": r[2]} for r in rows]
