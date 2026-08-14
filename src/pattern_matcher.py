"""
pattern_matcher.py

Phase 3: Pattern Matcher Engine

A rule-based module that determines whether a new error belongs to a known pattern.
Returns the standard pattern name and the default correction rule.
"""

from typing import Tuple, Optional

def match_pattern(error_type: str, column_name: Optional[str]) -> Tuple[str, str]:
    """
    Maps an incoming error to a standardized pattern name and correction rule.
    Returns: (pattern_name, correction_rule)
    """
    col_str = str(column_name).lower() if column_name else ""
    
    if error_type == "invalid_date":
        return "INVALID_DATE_FORMAT", "normalize_date_format"
    
    elif error_type == "invalid_date_unrecoverable":
        return "UNRECOVERABLE_DATE_FORMAT", "none"
        
    elif error_type == "duplicate_row":
        return "DUPLICATE_ROW", "remove_duplicate_row"
        
    elif error_type == "whitespace":
        return "WHITESPACE_INCONSISTENCY", "trim_whitespace"
        
    elif error_type == "missing_date":
        return "MISSING_DATE_VALUE", "none"
        
    elif error_type == "missing_numeric":
        return "MISSING_VALUE_NUMERIC", "fill_with_median"
        
    elif error_type == "missing_text":
        return "MISSING_VALUE_TEXT", "fill_with_unknown"
        
    elif error_type == "empty_string":
        return "EMPTY_STRING", "normalize_empty_strings_to_na"
        
    return "UNKNOWN_PATTERN", "none"
