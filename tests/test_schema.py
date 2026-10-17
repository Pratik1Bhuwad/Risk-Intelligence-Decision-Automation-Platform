"""
Tests for schema audit and semantic role inference.
"""

from src.config import AuditConfig
from src.audit.schema import audit_schema, infer_semantic_category


def test_infer_semantic_category():
    cfg = AuditConfig()
    assert infer_semantic_category("step", cfg) == "TEMPORAL_STEP"
    assert infer_semantic_category("type", cfg) == "CATEGORICAL_TRANSACTION_TYPE"
    assert infer_semantic_category("nameOrig", cfg) == "ENTITY_ID_ORIGIN"
    assert infer_semantic_category("nameDest", cfg) == "ENTITY_ID_DEST"
    assert infer_semantic_category("isFraud", cfg) == "TARGET_BINARY"
    assert infer_semantic_category("isFlaggedFraud", cfg) == "FLAG_BINARY"
    assert infer_semantic_category("amount", cfg) == "NUMERICAL_AMOUNT"
    assert infer_semantic_category("oldbalanceOrg", cfg) == "NUMERICAL_BALANCE"
    assert infer_semantic_category("unknown_col", cfg) == "UNKNOWN"


def test_audit_schema(synthetic_df, test_config):
    schema_df = audit_schema(synthetic_df, test_config)
    assert len(schema_df) == 11
    assert set(schema_df["column_name"]) == set(synthetic_df.columns)
    assert all(schema_df["null_count"] == 0)
    assert all(schema_df["non_null_count"] == 10)
    assert all(schema_df["status"] == "CONFIRMED")
