"""
Tests for cardinality audit module.
"""

from src.audit.cardinality import audit_cardinality


def test_cardinality(synthetic_df, test_config):
    card_df = audit_cardinality(synthetic_df, test_config)
    assert len(card_df) > 0
    assert "nameOrig" in card_df["column"].values
    assert "nameDest" in card_df["column"].values
    assert "type" in card_df["column"].values

    orig_row = card_df[card_df["column"] == "nameOrig"].iloc[0]
    assert orig_row["unique_count"] == 9  # 10 rows, 1 repeat
    assert orig_row["total_count"] == 10
    assert orig_row["max_freq"] == 2
    assert orig_row["min_freq"] == 1
