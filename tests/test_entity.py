"""
Tests for customer and account entity history audit.
"""

from src.audit.entity import audit_entity


def test_entity_audit(synthetic_df, test_config):
    entity_df = audit_entity(synthetic_df, test_config)
    assert len(entity_df) > 0

    orig_rows = entity_df[entity_df["entity_role"] == "ORIGINATING_ACCOUNT"]
    assert len(orig_rows) >= 3

    # In synthetic fixture, 9 unique originators out of 10, 8 single-tx, 1 repeat (C10001)
    single_row = orig_rows[
        orig_rows["metric"] == "SINGLE_TRANSACTION_ENTITIES"
    ].iloc[0]
    assert single_row["value"] == 8

    repeat_row = orig_rows[
        orig_rows["metric"] == "REPEAT_TRANSACTION_ENTITIES"
    ].iloc[0]
    assert repeat_row["value"] == 1

    dest_rows = entity_df[entity_df["entity_role"] == "DESTINATION_ACCOUNT"]
    assert len(dest_rows) >= 3
