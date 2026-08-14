"""
test_schema_processing.py

Phase 5A Tests
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_path))

from schema_validator import validate_schema

def test_missing_required_column():
    schema = {
        "policy": "STRICT",
        "columns": {
            "id": {"type": "integer", "required": True},
            "name": {"type": "string", "required": True}
        }
    }
    df = pd.DataFrame({"id": [1, 2]})
    is_valid, err = validate_schema(df, schema)
    assert not is_valid
    assert "Missing required columns: name" in err

def test_unexpected_column_strict():
    schema = {
        "policy": "STRICT",
        "columns": {
            "id": {"type": "integer", "required": True}
        }
    }
    df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    is_valid, err = validate_schema(df, schema)
    assert not is_valid
    assert "Unexpected columns found: name" in err

def test_unexpected_column_evolution():
    schema = {
        "policy": "EVOLUTION_ALLOWED",
        "columns": {
            "id": {"type": "integer", "required": True}
        }
    }
    df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    is_valid, err = validate_schema(df, schema)
    assert is_valid
    assert err == ""

def test_type_mismatch():
    schema = {
        "policy": "STRICT",
        "columns": {
            "id": {"type": "integer", "required": True}
        }
    }
    df = pd.DataFrame({"id": ["A", "B"]})
    is_valid, err = validate_schema(df, schema)
    assert not is_valid
    assert "Type mismatch in column 'id'" in err
