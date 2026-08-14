"""
pattern_library.py
"""
from pathlib import Path
from database import get_pattern, insert_pattern, update_pattern_frequency, list_patterns

def process_error_for_pattern(dataset_id: str, error_type: str, column_name: str, pattern_name: str, correction_rule: str) -> str:
    pattern = get_pattern(dataset_id, pattern_name)
    if pattern:
        update_pattern_frequency(pattern_name)
        return pattern["correction_rule"]
    else:
        db_column = column_name if column_name is not None else ""
        insert_pattern(dataset_id, pattern_name, error_type, db_column, correction_rule)
        return correction_rule

def generate_pattern_report(dataset_id: str, total_errors: int, auto_fixed_errors: int) -> str:
    patterns = [p for p in list_patterns() if p['dataset_id'] == dataset_id]
    lines = []
    lines.append(f"--- AutoRecoverDQ: Pattern Intelligence Report ({dataset_id}) ---")
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
    
    report_dir = Path(__file__).resolve().parent.parent / "logs" / dataset_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "pattern_report.txt"
    report_path.write_text(report_text, encoding="utf-8")
    return report_text
