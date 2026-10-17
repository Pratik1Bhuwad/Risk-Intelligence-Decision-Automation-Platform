"""
Tests for target distribution audit module.
"""

from src.audit.target import audit_target


def test_target_audit(synthetic_df, test_config):
    target_df = audit_target(synthetic_df, test_config)
    assert len(target_df) > 0

    overall_row = target_df[target_df["analysis_level"] == "OVERALL"].iloc[0]
    assert overall_row["total_count"] == 10
    assert overall_row["fraud_count"] == 5
    assert overall_row["fraud_rate_pct"] == 50.0
    assert overall_row["status"] == "CONFIRMED"

    # Transaction type breakdown
    transfer_rows = target_df[target_df["group_name"] == "TRANSFER"]
    assert len(transfer_rows) == 1
    assert transfer_rows.iloc[0]["fraud_count"] == 3
