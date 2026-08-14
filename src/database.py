"""
database.py

Handles everything related to the SQLite database.
Updated in Phase 4 to include quarantine_logs and extended recovery_logs.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

DB_PATH = Path(__file__).resolve().parent.parent / "logs" / "error_logs.db"

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_database() -> None:
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

    # recovery_logs table (Phase 2 & 4)
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
            recovery_status TEXT NOT NULL,
            retry_attempt INTEGER DEFAULT 1,
            final_status TEXT
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

    # quarantine_logs table (Phase 4)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quarantine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            row_number INTEGER,
            pattern_name TEXT,
            error_type TEXT NOT NULL,
            original_data TEXT,
            retry_count INTEGER,
            failure_reason TEXT
        )
    """)

    conn.commit()
    conn.close()

# --- Phase 4 Quarantine Helpers ---

def log_quarantine_record(file_name: str, row_number: int, pattern_name: str, error_type: str, original_data: str, retry_count: int, failure_reason: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO quarantine_logs 
        (timestamp, file_name, row_number, pattern_name, error_type, original_data, retry_count, failure_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, file_name, row_number, pattern_name, error_type, original_data, retry_count, failure_reason))
    conn.commit()
    conn.close()

# --- Phase 3 Pattern Library Helpers ---
def get_pattern(pattern_name: str) -> Optional[Dict]:
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
            "correction_rule": row[4]
        }
    return None

def insert_pattern(pattern_name: str, error_type: str, column_name: str, correction_rule: str) -> None:
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pattern_name, frequency, correction_rule FROM error_patterns ORDER BY frequency DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"pattern_name": r[0], "frequency": r[1], "correction_rule": r[2]} for r in rows]
