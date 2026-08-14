"""
main.py

Entry point for AutoRecoverDQ - Phase 1, 2, 3, and 4 (Self-Healing ETL).
"""

import sys
from pathlib import Path

from database import initialize_database
from ingest import read_csv_file
from validator import validate_dataframe
from logger import log_errors, log_recoveries
from recovery import recover_dataframe
from pattern_library import generate_pattern_report
from retry_engine import evaluate_and_retry

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def generate_recovery_report(metrics: dict) -> None:
    """Generates the Phase 4 Recovery Metrics Report."""
    lines = [
        "--- AutoRecoverDQ: Pipeline Recovery Summary ---",
        f"Rows processed: {metrics['rows_processed']}",
        f"Automatically repaired: {metrics['auto_repaired']}",
        f"Retried successfully: {metrics['retried_success']}",
        f"Sent to quarantine: {metrics['quarantined']}",
        f"Pipeline completion rate: {metrics['pipeline_completion']:.0f}%",
        f"Recovery success rate: {metrics['recovery_rate']:.1f}%",
        "------------------------------------------------\n"
    ]
    report_text = "\n".join(lines)
    print(report_text)
    
    report_path = BASE_DIR / "logs" / "recovery_report.txt"
    report_path.write_text(report_text, encoding="utf-8")


def run_pipeline(file_name: str) -> None:
    initialize_database()
    raw_path = RAW_DIR / file_name
    df = read_csv_file(raw_path)
    
    # Phase 1 - Validation
    errors, summary = validate_dataframe(df)
    log_errors(errors, file_name=file_name, pipeline_stage="validation")

    # Phase 2 & 3 - Automatic correction and pattern intelligence
    cleaned_df, recoveries, recovery_summary = recover_dataframe(df)
    
    # Phase 4 - Retry Engine & Quarantine
    final_safe_df, retry_metrics = evaluate_and_retry(df, cleaned_df, recoveries, file_name)
    
    # Log extended Phase 4 recoveries
    log_recoveries(recoveries, file_name=file_name)
    
    # Load safe records to clean dataset
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_path = PROCESSED_DIR / f"{Path(file_name).stem}_cleaned.csv"
    final_safe_df.to_csv(cleaned_path, index=False)
    
    # Generate Reports
    generate_pattern_report(summary['total_errors'], retry_metrics['auto_repaired'])
    generate_recovery_report(retry_metrics)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <file_name_in_data_raw>")
        sys.exit(1)
    run_pipeline(sys.argv[1])
