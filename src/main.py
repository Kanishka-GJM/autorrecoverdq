"""
main.py
"""
import sys
from pathlib import Path

from database import initialize_database, log_pipeline_run
from ingest import read_csv_file
from validator import validate_dataframe
from logger import log_errors, log_recoveries
from recovery import recover_dataframe
from pattern_library import generate_pattern_report
from retry_engine import evaluate_and_retry
from schema_registry import get_schema
from schema_validator import validate_schema

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def generate_recovery_report(dataset_id: str, metrics: dict) -> None:
    lines = [
        f"--- AutoRecoverDQ: Pipeline Recovery Summary ({dataset_id}) ---",
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
    
    report_dir = BASE_DIR / "logs" / dataset_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "recovery_report.txt"
    report_path.write_text(report_text, encoding="utf-8")

def identify_dataset(file_name: str) -> str:
    stem = Path(file_name).stem
    if stem.startswith("customers"): return "customers"
    if stem.startswith("orders"): return "orders"
    if stem.startswith("products"): return "products"
    return stem.split('_')[0]

def run_pipeline(file_name: str, dataset_id: str = None) -> None:
    initialize_database()
    raw_path = RAW_DIR / file_name
    
    if dataset_id is None:
        dataset_id = identify_dataset(file_name)
        
    try:
        schema = get_schema(dataset_id)
    except ValueError as e:
        print(f"Error: {e}")
        log_pipeline_run(dataset_id, "unknown", file_name, "FAILED_SCHEMA_NOT_FOUND", 0, 0, 0)
        return
        
    schema_version = schema.get("version", "v1")
    df = read_csv_file(raw_path)
    
    # Phase 5A - Schema Validation
    is_valid, schema_error = validate_schema(df, schema)
    if not is_valid:
        print(f"Schema Validation Failed for {file_name}: {schema_error}")
        log_pipeline_run(dataset_id, schema_version, file_name, "FAILED_SCHEMA_VALIDATION", len(df), 0, len(df))
        return
    
    # Phase 1 - Validation
    errors, summary = validate_dataframe(df)
    log_errors(errors, file_name=file_name, dataset_id=dataset_id, schema_version=schema_version, pipeline_stage="validation")

    # Phase 2 & 3 - Automatic correction and pattern intelligence
    cleaned_df, recoveries, recovery_summary = recover_dataframe(df, dataset_id)
    
    # Phase 4 - Retry Engine & Quarantine
    final_safe_df, retry_metrics = evaluate_and_retry(df, cleaned_df, recoveries, file_name, dataset_id, schema_version)
    
    # Log extended Phase 4 recoveries
    log_recoveries(recoveries, file_name=file_name, dataset_id=dataset_id, schema_version=schema_version)
    
    # Load safe records to clean dataset specific folder
    processed_ds_dir = PROCESSED_DIR / dataset_id
    processed_ds_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = processed_ds_dir / f"{Path(file_name).stem}_cleaned.csv"
    final_safe_df.to_csv(cleaned_path, index=False)
    
    # Generate Reports
    generate_pattern_report(dataset_id, summary['total_errors'], retry_metrics['auto_repaired'])
    generate_recovery_report(dataset_id, retry_metrics)
    
    # Log Pipeline Run
    log_pipeline_run(
        dataset_id=dataset_id,
        schema_version=schema_version,
        source_file=file_name,
        status="SUCCESS",
        rows_processed=retry_metrics['rows_processed'],
        rows_repaired=retry_metrics['retried_success'],
        rows_quarantined=retry_metrics['quarantined']
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <file_name_in_data_raw> [dataset_id]")
        sys.exit(1)
    ds_id = sys.argv[2] if len(sys.argv) > 2 else None
    run_pipeline(sys.argv[1], ds_id)
