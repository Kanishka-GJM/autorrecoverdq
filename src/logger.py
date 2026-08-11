"""
logger.py

Responsible for writing detected data quality errors into the
error_logs SQLite table. The validator produces plain dictionaries
describing each error; this file just persists them.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any

from database import get_connection


def log_errors(errors: List[Dict[str, Any]], file_name: str, pipeline_stage: str = "validation") -> None:
    """
    Insert a list of error records into the error_logs table.

    Each error dict is expected to have the keys:
        row_number, column_name, error_type, original_value

    Args:
        errors: list of error dictionaries produced by validator.py
        file_name: name of the CSV file being processed
        pipeline_stage: which stage of the pipeline logged the error
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
