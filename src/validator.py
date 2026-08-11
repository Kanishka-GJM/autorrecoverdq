"""
validator.py

Runs data quality checks over a DataFrame and returns a list of
error records (as plain dictionaries) describing every problem found.

Checks implemented in Phase 1:
    1. Missing values (NaN / None)
    2. Duplicate rows
    3. Invalid date format (for any column with "date" in its name)
    4. Empty strings in mandatory fields (all columns, in Phase 1)

Nothing is corrected here - this file only detects and reports.
"""

from datetime import datetime
from typing import List, Dict, Any, Tuple

import pandas as pd

# Any column whose name contains one of these substrings is treated
# as a date column and checked for valid formatting.
DATE_COLUMN_HINTS = ["date"]

# Formats we consider "valid" dates. Add more here as needed.
ACCEPTED_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]


def _is_valid_date(value: str) -> bool:
    """Return True if value matches one of the accepted date formats."""
    for fmt in ACCEPTED_DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def _find_date_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns that look like they should contain dates."""
    return [
        col for col in df.columns
        if any(hint in col.lower() for hint in DATE_COLUMN_HINTS)
    ]


def identify_date_columns(df: pd.DataFrame) -> List[str]:
    """Public wrapper for _find_date_columns."""
    return _find_date_columns(df)


def check_missing_values(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect missing (NaN/None) values in every column."""
    errors = []
    for col in df.columns:
        missing_mask = df[col].isna()
        for row_number in df.index[missing_mask]:
            errors.append({
                "row_number": int(row_number) + 1,  # 1-indexed for readability
                "column_name": col,
                "error_type": "missing_value",
                "original_value": None,
            })
    return errors


def check_duplicate_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect fully duplicated rows (keeping the first occurrence as original)."""
    errors = []
    duplicate_mask = df.duplicated(keep="first")
    for row_number in df.index[duplicate_mask]:
        errors.append({
            "row_number": int(row_number) + 1,
            "column_name": None,
            "error_type": "duplicate_row",
            "original_value": df.loc[row_number].to_dict(),
        })
    return errors


def check_invalid_dates(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect invalid or unparseable values in date-like columns."""
    errors = []
    for col in _find_date_columns(df):
        for row_number, value in df[col].items():
            if pd.isna(value):
                continue  # already caught by missing value check
            if not _is_valid_date(str(value)):
                errors.append({
                    "row_number": int(row_number) + 1,
                    "column_name": col,
                    "error_type": "invalid_date",
                    "original_value": value,
                })
    return errors


def check_empty_strings(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect empty or whitespace-only strings in mandatory fields.

    In Phase 1, every column is treated as mandatory.
    """
    errors = []
    for col in df.columns:
        for row_number, value in df[col].items():
            if pd.isna(value):
                continue  # already caught by missing value check
            if isinstance(value, str) and value.strip() == "":
                errors.append({
                    "row_number": int(row_number) + 1,
                    "column_name": col,
                    "error_type": "empty_string",
                    "original_value": value,
                })
    return errors


def validate_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run all validation checks on a DataFrame.

    Returns:
        A tuple of:
        - full list of error dicts (for logging to the database)
        - a summary dict with counts per error type (for the printed report)
    """
    missing = check_missing_values(df)
    duplicates = check_duplicate_rows(df)
    invalid_dates = check_invalid_dates(df)
    empty_strings = check_empty_strings(df)

    all_errors = missing + duplicates + invalid_dates + empty_strings

    summary = {
        "missing_values": len(missing),
        "duplicate_rows": len(duplicates),
        "invalid_dates": len(invalid_dates),
        "empty_strings": len(empty_strings),
        "total_errors": len(all_errors),
    }

    return all_errors, summary
