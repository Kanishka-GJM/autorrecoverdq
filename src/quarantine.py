"""
quarantine.py
"""
import pandas as pd
from pathlib import Path
from database import log_quarantine_record

def quarantine_records(original_df: pd.DataFrame, failed_row_indices: set, file_name: str, dataset_id: str, schema_version: str, reasons: dict) -> None:
    if not failed_row_indices:
        return
        
    quarantine_dir = Path(__file__).resolve().parent.parent / "data" / "quarantine" / dataset_id
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = quarantine_dir / f"{Path(file_name).stem}_quarantine.csv"
    
    quarantine_df = original_df.loc[list(failed_row_indices)].copy()
    if quarantine_path.exists():
        quarantine_df.to_csv(quarantine_path, mode='a', header=False, index=False)
    else:
        quarantine_df.to_csv(quarantine_path, index=False)
        
    for row_idx in failed_row_indices:
        row_data = str(original_df.loc[row_idx].to_dict())
        error_type, pattern_name, failure_reason = reasons.get(row_idx, ("unknown", "UNKNOWN", "Validation failed post-recovery"))
        log_quarantine_record(
            file_name=file_name,
            dataset_id=dataset_id,
            schema_version=schema_version,
            row_number=int(row_idx) + 1,
            pattern_name=pattern_name,
            error_type=error_type,
            original_data=row_data,
            retry_count=1,
            failure_reason=failure_reason
        )
