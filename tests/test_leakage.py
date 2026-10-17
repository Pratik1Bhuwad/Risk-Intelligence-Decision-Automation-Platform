"""
Tests for leakage assessment module.
"""

from src.audit.leakage import audit_leakage


def test_leakage_audit(synthetic_df, test_config):
    leak_df = audit_leakage(synthetic_df, test_config)
    assert len(leak_df) >= 7

    fields = set(leak_df["field"])
    assert "isFraud" in fields
    assert "isFlaggedFraud" in fields
    assert "newbalanceOrig" in fields
    assert "oldbalanceOrg" in fields

    # Check that isFlaggedFraud is INVESTIGATE
    flag_row = leak_df[leak_df["field"] == "isFlaggedFraud"].iloc[0]
    assert flag_row["status"] == "INVESTIGATE"
    assert "RULE_OUTPUT" in flag_row["suspected_leakage_type"]

    # Check that newbalanceOrig is INVESTIGATE
    newbal_row = leak_df[leak_df["field"] == "newbalanceOrig"].iloc[0]
    assert newbal_row["status"] == "INVESTIGATE"
    assert newbal_row["suspected_leakage_type"] == "POST_EVENT_LEAKAGE"
