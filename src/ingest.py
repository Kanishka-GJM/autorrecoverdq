"""
ingest.py

Responsible for reading raw CSV files into pandas DataFrames.
Kept intentionally simple in Phase 1 - later phases may extend this
to support multiple file formats or sources.
"""

from pathlib import Path
import pandas as pd


def read_csv_file(file_path: Path) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame.

    Args:
        file_path: path to the CSV file

    Returns:
        A DataFrame containing the raw data. All columns are read as
        strings (dtype=str) so that validation can inspect original
        values without pandas silently converting types (e.g. turning
        empty strings into NaN differently than we expect).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw file not found: {file_path}")

    df = pd.read_csv(file_path, dtype=str, keep_default_na=True)
    return df
