"""
Tests for temporal and chronological ordering audit.
"""

from src.audit.temporal import audit_temporal


def test_temporal_audit(synthetic_df, test_config):
    temp_df = audit_temporal(synthetic_df, test_config)
    assert len(temp_df) >= 4

    metrics = dict(zip(temp_df["metric"], temp_df["value"]))
    assert "TEMPORAL_RANGE" in metrics
    assert metrics["TEMPORAL_RANGE"] == "[1, 5]"
    assert metrics["UNIQUE_STEPS_OBSERVED"] == 5
    assert metrics["CHRONOLOGICAL_ORDERING_RAW_FILE"] == "MONOTONIC_INCREASING"
