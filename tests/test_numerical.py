"""
Tests for numerical distribution and data-quality checks.
"""

from src.audit.numerical import audit_numerical


def test_numerical_audit(synthetic_df, test_config):
    num_df = audit_numerical(synthetic_df, test_config)
    assert len(num_df) >= 5
    assert "amount" in num_df["column"].values
    assert "oldbalanceOrg" in num_df["column"].values

    amt_row = num_df[num_df["column"] == "amount"].iloc[0]
    assert amt_row["min"] == 25.5
    assert amt_row["max"] == 300000.0
    assert amt_row["negative_count"] == 0
    assert amt_row["infinite_count"] == 0
    assert amt_row["status"] == "OBSERVED"
    assert "p50" in amt_row
