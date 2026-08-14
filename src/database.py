"""
database.py

Handles everything related to the SQLite database.
Updated in Phase 5A to handle dataset_id, schema_version, and pipeline_runs.
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

    # Create tables if not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            source_file TEXT NOT NULL,
            status TEXT NOT NULL,
            rows_processed INTEGER,
            rows_repaired INTEGER,
            rows_quarantined INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            dataset_id TEXT,
            schema_version TEXT,
            row_number INTEGER,
            column_name TEXT,
            error_type TEXT NOT NULL,
            original_value TEXT,
            pipeline_stage TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            dataset_id TEXT,
            schema_version TEXT,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id TEXT,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quarantine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            dataset_id TEXT,
            schema_version TEXT,
            row_number INTEGER,
            pattern_name TEXT,
            error_type TEXT NOT NULL,
            original_data TEXT,
            retry_count INTEGER,
            failure_reason TEXT
        )
    """)

    # Attempt to safely add new columns to existing tables (in case they already exist from Phase 1-4)
    tables_to_upgrade = {
        "error_logs": ["dataset_id TEXT", "schema_version TEXT"],
        "recovery_logs": ["dataset_id TEXT", "schema_version TEXT"],
        "error_patterns": ["dataset_id TEXT"],
        "quarantine_logs": ["dataset_id TEXT", "schema_version TEXT"]
    }
    
    for table, columns in tables_to_upgrade.items():
        for col_def in columns:
            col_name = col_def.split()[0]
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            except sqlite3.OperationalError:
                pass # Column already exists

    conn.commit()
    conn.close()

def log_pipeline_run(dataset_id: str, schema_version: str, source_file: str, status: str, rows_processed: int, rows_repaired: int, rows_quarantined: int):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO pipeline_runs 
        (timestamp, dataset_id, schema_version, source_file, status, rows_processed, rows_repaired, rows_quarantined)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, dataset_id, schema_version, source_file, status, rows_processed, rows_repaired, rows_quarantined))
    conn.commit()
    conn.close()

def log_quarantine_record(file_name: str, dataset_id: str, schema_version: str, row_number: int, pattern_name: str, error_type: str, original_data: str, retry_count: int, failure_reason: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO quarantine_logs 
        (timestamp, file_name, dataset_id, schema_version, row_number, pattern_name, error_type, original_data, retry_count, failure_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, file_name, dataset_id, schema_version, row_number, pattern_name, error_type, original_data, retry_count, failure_reason))
    conn.commit()
    conn.close()

def get_pattern(dataset_id: str, pattern_name: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM error_patterns WHERE pattern_name=? AND dataset_id=?", (pattern_name, dataset_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "dataset_id": row[1],
            "pattern_name": row[2],
            "error_type": row[3],
            "column_name": row[4],
            "correction_rule": row[5]
        }
    return None

def insert_pattern(dataset_id: str, pattern_name: str, error_type: str, column_name: str, correction_rule: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute("""
            INSERT INTO error_patterns 
            (dataset_id, pattern_name, error_type, column_name, correction_rule, frequency, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (dataset_id, pattern_name, error_type, column_name, correction_rule, now, now))
    except sqlite3.IntegrityError:
        pass
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
    cursor.execute("SELECT dataset_id, pattern_name, frequency, correction_rule FROM error_patterns ORDER BY frequency DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"dataset_id": r[0], "pattern_name": r[1], "frequency": r[2], "correction_rule": r[3]} for r in rows]
