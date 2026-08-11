"""
logger.py

Responsible for writing detected data quality errors into the
error_logs SQLite table. The validator produces plain dictionaries
 describing each error; this file just persists them.

Phase 2 adds logging of recovery records.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any

from database import get_connection


def log_errors(errors: List[Dict[str, Any]], file_name: str, pipeline_stage: str = "validation") -> None:
    """Insert a list of error records into the error_logs table.

    Each error dict is expected to have the keys:
        row_number, column_name, error_type, original_value
    """
    if not errors:
        return

    conn = get_connection()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    rows_to_insert = [
        (
            timestamp,
            file_name,
            error.get("row_number"),
            error.get("column_name"),
            error.get("error_type"),
            str(error.get("original_value")),
            pipeline_stage,
        )
        for error in errors
    ]

    cursor.executemany("""
        INSERT INTO error_logs (
            timestamp, file_name, row_number, column_name,
            error_type, original_value, pipeline_stage
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)

    conn.commit()
    conn.close()


def log_recoveries(recoveries: List[Dict[str, Any]], file_name: str) -> None:
    """Insert a list of correction records into the recovery_logs table.

    Each recovery dict is expected to have the keys:
        row_number, column_name, error_type, correction_applied,
        original_value, corrected_value, recovery_status
    """
    if not recoveries:
        return

    conn = get_connection()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    rows_to_insert = [
        (
            timestamp,
            file_name,
            recovery.get("row_number"),
            recovery.get("column_name"),
            recovery.get("error_type"),
            recovery.get("correction_applied"),
            str(recovery.get("original_value")),
            str(recovery.get("corrected_value")),
            recovery.get("recovery_status"),
        )
        for recovery in recoveries
    ]

    cursor.executemany("""
        INSERT INTO recovery_logs (
            timestamp, file_name, row_number, column_name, error_type,
            correction_applied, original_value, corrected_value, recovery_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)

    conn.commit()
    conn.close()
