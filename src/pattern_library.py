"""
pattern_library.py

Phase 3: Pattern Library

Responsible for storing, updating, and retrieving recurring error patterns.
Generates the Pattern Intelligence Report.
"""

from pathlib import Path
from database import get_pattern, insert_pattern, update_pattern_frequency, list_patterns

def process_error_for_pattern(error_type: str, column_name: str, pattern_name: str, correction_rule: str) -> str:
    """
    Checks if a pattern exists in the library.
    If it exists, increments its frequency.
    If it doesn't, registers a new pattern.
    Returns the correction rule that should be applied.
    """
    pattern = get_pattern(pattern_name)
    if pattern:
        update_pattern_frequency(pattern_name)
        return pattern["correction_rule"]
    else:
        # Save None column_name as an empty string for the database
        db_column = column_name if column_name is not None else ""
        insert_pattern(pattern_name, error_type, db_column, correction_rule)
        return correction_rule

def generate_pattern_report(total_errors: int, auto_fixed_errors: int) -> str:
    """
    Generates the Pattern Intelligence Report and saves it to logs/pattern_report.txt.
    """
    patterns = list_patterns()
    lines = []
    lines.append("--- AutoRecoverDQ: Pattern Intelligence Report ---")
    lines.append("Pattern Summary")
    lines.append("-" * 50)
    
    for p in patterns:
        lines.append(f"{p['pattern_name']:<35} {p['frequency']} occurrences")
    
    lines.append("-" * 50)
    lines.append(f"Patterns learned: {len(patterns)}")
    
    coverage = (auto_fixed_errors / total_errors * 100) if total_errors > 0 else 100
    lines.append(f"Auto-fix coverage: {coverage:.0f}%")
    lines.append("--------------------------------------------------\n")
    
    report_text = "\n".join(lines)
    
    # Save to file
    report_path = Path(__file__).resolve().parent.parent / "logs" / "pattern_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    
    return report_text
