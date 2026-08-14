"""
quarantine.py

Phase 4: Quarantine Management

Handles isolating unrecoverable or failed records so they don't break the pipeline.
Quarantined records are written to a separate CSV and logged in the database.
"""

import pandas as pd
from pathlib import Path
from database import log_quarantine_record

QUARANTINE_DIR = Path(__file__).resolve().parent.parent / "data" / "quarantine"

def quarantine_records(original_df: pd.DataFrame, failed_row_indices: set, file_name: str, reasons: dict) -> None:
    """
    Moves failed rows into the quarantine dataset and logs them.
    `reasons` is a dict mapping row_index -> (error_type, pattern_name, failure_reason)
    """
    if not failed_row_indices:
        return
        
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    quarantine_path = QUARANTINE_DIR / f"{Path(file_name).stem}_quarantine.csv"
    
    quarantine_df = original_df.loc[list(failed_row_indices)].copy()
    
    # Append to CSV
    if quarantine_path.exists():
        quarantine_df.to_csv(quarantine_path, mode='a', header=False, index=False)
    else:
        quarantine_df.to_csv(quarantine_path, index=False)
        
    # Log to database
    for row_idx in failed_row_indices:
        row_data = str(original_df.loc[row_idx].to_dict())
        error_type, pattern_name, failure_reason = reasons.get(row_idx, ("unknown", "UNKNOWN", "Validation failed post-recovery"))
        log_quarantine_record(
            file_name=file_name,
            row_number=int(row_idx) + 1,
            pattern_name=pattern_name,
            error_type=error_type,
            original_data=row_data,
            retry_count=1,
            failure_reason=failure_reason
        )
