"""
main.py

Entry point for AutoRecoverDQ - Phase 1, 2, and 3 combined.
"""

import sys
from pathlib import Path

from database import initialize_database
from ingest import read_csv_file
from validator import validate_dataframe
from logger import log_errors, log_recoveries
from recovery import recover_dataframe
from pattern_library import generate_pattern_report

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def run_pipeline(file_name: str) -> None:
    """Run the full pipeline for a CSV file."""
    # Phase 1 - validation
    initialize_database()
    raw_path = RAW_DIR / file_name
    df = read_csv_file(raw_path)
    errors, summary = validate_dataframe(df)
    log_errors(errors, file_name=file_name, pipeline_stage="validation")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / file_name).write_text(df.to_csv(index=False), encoding="utf-8")
    print_summary(file_name, len(df), summary)

    # Phase 2 & 3 - automatic correction and pattern intelligence
    cleaned_df, recoveries, recovery_summary = recover_dataframe(df)
    log_recoveries(recoveries, file_name=file_name)
    cleaned_file_name = f"{Path(file_name).stem}_cleaned.csv"
    cleaned_path = PROCESSED_DIR / cleaned_file_name
    cleaned_df.to_csv(cleaned_path, index=False)
    print_recovery_report(file_name, len(df), recovery_summary)

    # Phase 3 - Pattern report generation
    total_errors = summary['total_errors']
    auto_fixed_errors = sum(1 for r in recoveries if r["recovery_status"] == "fixed")
    report_text = generate_pattern_report(total_errors, auto_fixed_errors)
    print("\n" + report_text + "\n")


def print_summary(file_name: str, rows_processed: int, summary: dict) -> None:
    print("\n--- AutoRecoverDQ: Processing Summary ---")
    print(f"File processed: {file_name}")
    print(f"Rows processed: {rows_processed}")
    print(f"Missing values: {summary['missing_values']}")
    print(f"Duplicate rows: {summary['duplicate_rows']}")
    print(f"Invalid dates: {summary['invalid_dates']}")
    print(f"Empty strings: {summary['empty_strings']}")
    print(f"Errors logged: {summary['total_errors']}")
    print("------------------------------------------\n")


def print_recovery_report(file_name: str, rows_processed: int, summary: dict) -> None:
    print("--- AutoRecoverDQ: Recovery Report ---")
    print(f"File processed: {file_name}")
    print(f"Rows processed: {rows_processed}")
    print(f"Invalid dates repaired: {summary['invalid_dates_repaired']}")
    print(f"Duplicate rows removed: {summary['duplicate_rows_removed']}")
    print(f"Missing values filled: {summary['missing_values_filled']}")
    print(f"Whitespace normalized: {summary['whitespace_normalized']}")
    print(f"Unrecoverable records: {summary['unrecoverable_records']}")
    print("----------------------------------------\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <file_name_in_data_raw>")
        sys.exit(1)
    run_pipeline(sys.argv[1])
