"""
main.py

Entry point for AutoRecoverDQ - Phase 1.

Pipeline steps:
    1. Initialize the SQLite database (creates error_logs table if needed)
    2. Read a raw CSV file from data/raw/
    3. Validate it (missing values, duplicates, invalid dates, empty strings)
    4. Log every detected error into error_logs.db
    5. Save an (unchanged, for now) copy of the data into data/processed/
    6. Print a summary of what was found

Usage:
    python src/main.py orders.csv
"""

import sys
from pathlib import Path

from database import initialize_database
from ingest import read_csv_file
from validator import validate_dataframe
from logger import log_errors

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def run_pipeline(file_name: str) -> None:
    """Run the full Phase 1 pipeline for a single CSV file."""

    # Step 1: make sure the database and table exist
    initialize_database()

    # Step 2: read the raw file
    raw_path = RAW_DIR / file_name
    df = read_csv_file(raw_path)

    # Step 3: validate
    errors, summary = validate_dataframe(df)

    # Step 4: log errors to the database
    log_errors(errors, file_name=file_name, pipeline_stage="validation")

    # Step 5: save a copy of the dataset to processed/
    # (Phase 1 does not correct anything yet, so this is an unmodified copy)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    processed_path = PROCESSED_DIR / file_name
    df.to_csv(processed_path, index=False)

    # Step 6: print a concise summary
    print_summary(file_name, len(df), summary)


def print_summary(file_name: str, rows_processed: int, summary: dict) -> None:
    """Print a concise, human-readable processing summary."""
    print("\n--- AutoRecoverDQ: Processing Summary ---")
    print(f"File processed: {file_name}")
    print(f"Rows processed: {rows_processed}")
    print(f"Missing values: {summary['missing_values']}")
    print(f"Duplicate rows: {summary['duplicate_rows']}")
    print(f"Invalid dates: {summary['invalid_dates']}")
    print(f"Empty strings: {summary['empty_strings']}")
    print(f"Errors logged: {summary['total_errors']}")
    print("------------------------------------------\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <file_name_in_data_raw>")
        sys.exit(1)

    input_file_name = sys.argv[1]
    run_pipeline(input_file_name)
