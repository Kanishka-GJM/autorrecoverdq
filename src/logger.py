"""
logger.py
"""

from datetime import datetime, timezone
from typing import List, Dict, Any

from database import get_connection

def log_errors(errors: List[Dict[str, Any]], file_name: str, dataset_id: str, schema_version: str, pipeline_stage: str = "validation") -> None:
    if not errors:
        return
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()
    rows_to_insert = [
        (
            timestamp, file_name, dataset_id, schema_version,
            error.get("row_number"), error.get("column_name"),
            error.get("error_type"), str(error.get("original_value")), pipeline_stage,
        )
        for error in errors
    ]
    cursor.executemany("""
        INSERT INTO error_logs (
            timestamp, file_name, dataset_id, schema_version, row_number, column_name,
            error_type, original_value, pipeline_stage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)
    conn.commit()
    conn.close()

def log_recoveries(recoveries: List[Dict[str, Any]], file_name: str, dataset_id: str, schema_version: str) -> None:
    if not recoveries:
        return
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()
    rows_to_insert = [
        (
            timestamp, file_name, dataset_id, schema_version,
            recovery.get("row_number"), recovery.get("column_name"),
            recovery.get("error_type"), recovery.get("correction_applied"),
            str(recovery.get("original_value")), str(recovery.get("corrected_value")),
            recovery.get("recovery_status"), recovery.get("retry_attempt", 1),
            recovery.get("final_status", "PENDING")
        )
        for recovery in recoveries
    ]
    cursor.executemany("""
        INSERT INTO recovery_logs (
            timestamp, file_name, dataset_id, schema_version, row_number, column_name, error_type,
            correction_applied, original_value, corrected_value, recovery_status,
            retry_attempt, final_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)
    conn.commit()
    conn.close()
