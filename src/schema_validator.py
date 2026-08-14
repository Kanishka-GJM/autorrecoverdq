"""
schema_validator.py

Validates an incoming dataframe against its registered schema.
Detects missing required columns, unexpected columns (handles STRICT vs EVOLUTION_ALLOWED),
and checks basic data types.
"""

import pandas as pd
from typing import Dict, Any, Tuple

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates df against the schema.
    Returns (is_valid, error_message).
    """
    expected_columns = schema.get("columns", {})
    policy = schema.get("policy", "STRICT")
    
    required_cols = [col for col, props in expected_columns.items() if props.get("required", False)]
    
    # 1. Check Missing Required Columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}"
        
    # 2. Check Unexpected Columns
    unexpected_cols = [col for col in df.columns if col not in expected_columns]
    if unexpected_cols:
        if policy == "STRICT":
            return False, f"STRICT Policy violation. Unexpected columns found: {', '.join(unexpected_cols)}"
        else:
            print(f"Schema Evolution Log: Accepted unexpected columns {unexpected_cols}")
            
    # 3. Check Data Types (Best effort type checking)
    for col in df.columns:
        if col not in expected_columns:
            continue
            
        expected_type = expected_columns[col].get("type", "string")
        non_null_values = df[col].dropna()
        if non_null_values.empty:
            continue
            
        if expected_type == "integer":
            try:
                pd.to_numeric(non_null_values, downcast='integer', errors='raise')
            except ValueError:
                return False, f"Type mismatch in column '{col}': expected integer"
        elif expected_type == "float":
            try:
                pd.to_numeric(non_null_values, downcast='float', errors='raise')
            except ValueError:
                return False, f"Type mismatch in column '{col}': expected float"
                
    return True, ""
