"""
recovery.py

Phase 2 & 3: Automatic Correction Engine with Pattern Intelligence.

Takes a DataFrame that has already been through validation (Phase 1) and applies
safe, deterministic repairs.

Phase 3 Update: Every correction now matches the error to a known pattern,
retrieves the correction rule from the Pattern Library, and updates statistics.
"""

from datetime import datetime
from typing import List, Dict, Any, Tuple

import pandas as pd

from validator import identify_date_columns
from pattern_matcher import match_pattern
from pattern_library import process_error_for_pattern

# Date formats we attempt to parse (order matters)
CANDIDATE_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d/%m/%y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
]

TARGET_DATE_FORMAT = "%Y-%m-%d"


def _make_record(row_number: int, column_name: Any, error_type: str,
                 correction_applied: str, original_value: Any,
                 corrected_value: Any, recovery_status: str) -> Dict[str, Any]:
    """Helper to build a recovery-record dict consistently."""
    return {
        "row_number": row_number,
        "column_name": column_name,
        "error_type": error_type,
        "correction_applied": correction_applied,
        "original_value": original_value,
        "corrected_value": corrected_value,
        "recovery_status": recovery_status,
    }


def _try_parse_date(value: str) -> str | None:
    """Return a YYYY-MM-DD string if `value` matches any known format."""
    for fmt in CANDIDATE_DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime(TARGET_DATE_FORMAT)
        except ValueError:
            continue
    return None


def trim_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Trim leading/trailing whitespace from every string column."""
    df = df.copy()
    records: List[Dict[str, Any]] = []
    for col in df.columns:
        for row_number, value in df[col].items():
            if not isinstance(value, str):
                continue
            trimmed = value.strip()
            if trimmed != value:
                # Phase 3 Pattern Registration
                pattern_name, default_rule = match_pattern("whitespace", col)
                rule_to_apply = process_error_for_pattern("whitespace", col, pattern_name, default_rule)
                
                records.append(_make_record(
                    row_number=int(row_number) + 1,
                    column_name=col,
                    error_type="whitespace",
                    correction_applied=rule_to_apply,
                    original_value=value,
                    corrected_value=trimmed,
                    recovery_status="fixed",
                ))
                df.at[row_number, col] = trimmed
    return df, records


def normalize_empty_strings_to_na(df: pd.DataFrame) -> pd.DataFrame:
    """Convert empty/blank strings to NaN so they are handled by the fill step."""
    df = df.copy()
    for col in df.columns:
        blank_mask = df[col].apply(lambda v: isinstance(v, str) and v.strip() == "")
        df.loc[blank_mask, col] = pd.NA
    return df


def normalize_dates(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Reformat date-like columns to YYYY-MM-DD; log unrecoverable values."""
    df = df.copy()
    records: List[Dict[str, Any]] = []
    date_columns = identify_date_columns(df)
    for col in date_columns:
        for row_number, value in df[col].items():
            if pd.isna(value):
                continue
            normalized = _try_parse_date(str(value))
            if normalized is None:
                # Phase 3 Pattern Registration
                pattern_name, default_rule = match_pattern("invalid_date_unrecoverable", col)
                rule_to_apply = process_error_for_pattern("invalid_date", col, pattern_name, default_rule)
                
                records.append(_make_record(
                    row_number=int(row_number) + 1,
                    column_name=col,
                    error_type="invalid_date",
                    correction_applied=rule_to_apply,
                    original_value=value,
                    corrected_value=value,
                    recovery_status="unrecoverable",
                ))
            elif normalized != value:
                # Phase 3 Pattern Registration
                pattern_name, default_rule = match_pattern("invalid_date", col)
                rule_to_apply = process_error_for_pattern("invalid_date", col, pattern_name, default_rule)
                
                records.append(_make_record(
                    row_number=int(row_number) + 1,
                    column_name=col,
                    error_type="invalid_date",
                    correction_applied=rule_to_apply,
                    original_value=value,
                    corrected_value=normalized,
                    recovery_status="fixed",
                ))
                df.at[row_number, col] = normalized
    return df, records


def fill_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Fill NaNs deterministically (numeric -> median, text -> "UNKNOWN")."""
    df = df.copy()
    records: List[Dict[str, Any]] = []
    date_columns = set(identify_date_columns(df))
    for col in df.columns:
        missing_mask = df[col].isna()
        if not missing_mask.any():
            continue
        if col in date_columns:
            pattern_name, default_rule = match_pattern("missing_date", col)
            for row_number in df.index[missing_mask]:
                rule_to_apply = process_error_for_pattern("missing_value", col, pattern_name, default_rule)
                records.append(_make_record(
                    row_number=int(row_number) + 1,
                    column_name=col,
                    error_type="missing_value",
                    correction_applied=rule_to_apply,
                    original_value=None,
                    corrected_value=None,
                    recovery_status="unrecoverable",
                ))
            continue
            
        # Determine if column is numeric
        non_null = df.loc[~missing_mask, col]
        numeric = pd.to_numeric(non_null, errors="coerce")
        is_numeric = non_null.shape[0] > 0 and numeric.notna().all()
        
        if is_numeric:
            fill_value = str(numeric.median())
            pattern_name, default_rule = match_pattern("missing_numeric", col)
        else:
            fill_value = "UNKNOWN"
            pattern_name, default_rule = match_pattern("missing_text", col)
            
        for row_number in df.index[missing_mask]:
            rule_to_apply = process_error_for_pattern("missing_value", col, pattern_name, default_rule)
            records.append(_make_record(
                row_number=int(row_number) + 1,
                column_name=col,
                error_type="missing_value",
                correction_applied=rule_to_apply,
                original_value=None,
                corrected_value=fill_value,
                recovery_status="fixed",
            ))
        df.loc[missing_mask, col] = fill_value
    return df, records


def remove_duplicate_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Drop fully duplicated rows, keeping the first occurrence."""
    duplicate_mask = df.duplicated(keep="first")
    records: List[Dict[str, Any]] = []
    for row_number in df.index[duplicate_mask]:
        # Phase 3 Pattern Registration
        pattern_name, default_rule = match_pattern("duplicate_row", None)
        rule_to_apply = process_error_for_pattern("duplicate_row", None, pattern_name, default_rule)
        
        records.append(_make_record(
            row_number=int(row_number) + 1,
            column_name=None,
            error_type="duplicate_row",
            correction_applied=rule_to_apply,
            original_value=df.loc[row_number].to_dict(),
            corrected_value=None,
            recovery_status="fixed",
        ))
    cleaned_df = df[~duplicate_mask].reset_index(drop=True)
    return cleaned_df, records


def recover_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, int]]:
    """Run the full Phase 2/3 correction pipeline on a DataFrame.
    Returns cleaned DataFrame, full recovery record list, and a summary dict.
    """
    working_df = df.copy()
    all_records: List[Dict[str, Any]] = []

    # 1. Whitespace
    working_df, whitespace_records = trim_whitespace(working_df)
    all_records.extend(whitespace_records)

    # 2. Empty strings -> NaN
    working_df = normalize_empty_strings_to_na(working_df)

    # 3. Dates
    working_df, date_records = normalize_dates(working_df)
    all_records.extend(date_records)

    # 4. Missing values
    working_df, missing_records = fill_missing_values(working_df)
    all_records.extend(missing_records)

    # 5. Duplicates
    working_df, duplicate_records = remove_duplicate_rows(working_df)
    all_records.extend(duplicate_records)

    summary = {
        "invalid_dates_repaired": sum(1 for r in date_records if r["recovery_status"] == "fixed"),
        "duplicate_rows_removed": len(duplicate_records),
        "missing_values_filled": sum(1 for r in missing_records if r["recovery_status"] == "fixed"),
        "whitespace_normalized": len(whitespace_records),
        "unrecoverable_records": sum(1 for r in all_records if r["recovery_status"] == "unrecoverable"),
    }

    return working_df, all_records, summary
