"""
retry_engine.py

Phase 4: Retry Engine

Evaluates the success of the recovery process by re-validating the cleaned dataframe.
Determines which records are successfully self-healed and which must be quarantined.
"""

from typing import Tuple, List, Dict, Any, Set
import pandas as pd
from validator import validate_dataframe
from quarantine import quarantine_records

def evaluate_and_retry(original_df: pd.DataFrame, cleaned_df: pd.DataFrame, recoveries: List[Dict[str, Any]], file_name: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates the cleaned dataframe. Records that still fail validation or were 
    marked as unrecoverable are quarantined. Successful recoveries are logged.
    Returns the final safe dataframe (with quarantined rows removed) and metrics.
    """
    # 1. Re-validate to find rows that STILL have errors
    retry_errors, _ = validate_dataframe(cleaned_df)
    still_failing_indices = {e['row_number'] - 1 for e in retry_errors}
    
    # 2. Identify rows that the recovery engine explicitly couldn't fix
    unrecoverable_indices = {r['row_number'] - 1 for r in recoveries if r['recovery_status'] == 'unrecoverable'}
    
    # 3. Combine to find all quarantined rows
    quarantine_indices = still_failing_indices.union(unrecoverable_indices)
    
    # 4. Update recovery logs with final statuses
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
            
    # 5. Execute Quarantine
    quarantine_records(original_df, quarantine_indices, file_name, quarantine_reasons)
    
    # 6. Drop quarantined rows from the final clean dataframe to ensure pipeline continuation
    final_df = cleaned_df.drop(index=list(quarantine_indices)).reset_index(drop=True)
    
    metrics = {
        "rows_processed": len(original_df),
        "auto_repaired": auto_repaired_count,
        "retried_success": retried_success_count,
        "quarantined": len(quarantine_indices),
        "pipeline_completion": 100.0,  # Pipeline always finishes
        "recovery_rate": (retried_success_count / len(recoveries) * 100) if recoveries else 100.0
    }
    
    return final_df, metrics
