"""
schema_registry.py

Loads and manages dataset schemas for Phase 5A.
"""

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
SCHEMA_FILE = CONFIG_DIR / "schemas.json"

def load_all_schemas() -> Dict[str, Any]:
    """Loads the entire schema registry."""
    if not SCHEMA_FILE.exists():
        return {}
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_schema(dataset_id: str) -> Dict[str, Any]:
    """Retrieves the schema definition for a specific dataset."""
    schemas = load_all_schemas()
    if dataset_id not in schemas:
        raise ValueError(f"Schema for dataset '{dataset_id}' not found in registry.")
    return schemas[dataset_id]
