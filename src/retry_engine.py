"""
retry_engine.py
"""
from typing import Tuple, List, Dict, Any, Set
import pandas as pd
from validator import validate_dataframe
from quarantine import quarantine_records

def evaluate_and_retry(original_df: pd.DataFrame, cleaned_df: pd.DataFrame, recoveries: List[Dict[str, Any]], file_name: str, dataset_id: str, schema_version: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    retry_errors, _ = validate_dataframe(cleaned_df)
    still_failing_indices = {e['row_number'] - 1 for e in retry_errors}
    unrecoverable_indices = {r['row_number'] - 1 for r in recoveries if r['recovery_status'] == 'unrecoverable'}
    quarantine_indices = still_failing_indices.union(unrecoverable_indices)
    
    quarantine_reasons = {}
    auto_repaired_count = 0
    retried_success_count = 0
    
    for r in recoveries:
        row_idx = r['row_number'] - 1
        r['retry_attempt'] = 1
        if row_idx in quarantine_indices:
            r['final_status'] = 'QUARANTINED'
            reason = "Unrecoverable" if r['recovery_status'] == 'unrecoverable' else "Failed retry validation"
            quarantine_reasons[row_idx] = (r['error_type'], r.get('pattern_name', 'UNKNOWN'), reason)
        else:
            r['final_status'] = 'RETRIED_SUCCESS'
            auto_repaired_count += 1
            retried_success_count += 1
            
    quarantine_records(original_df, quarantine_indices, file_name, dataset_id, schema_version, quarantine_reasons)
    indices_to_drop = [idx for idx in quarantine_indices if idx in cleaned_df.index]
    final_df = cleaned_df.drop(index=indices_to_drop).reset_index(drop=True)
    
    metrics = {
        "rows_processed": len(original_df),
        "auto_repaired": auto_repaired_count,
        "retried_success": retried_success_count,
        "quarantined": len(quarantine_indices),
        "pipeline_completion": 100.0,
        "recovery_rate": (retried_success_count / len(recoveries) * 100) if recoveries else 100.0
    }
    return final_df, metrics
