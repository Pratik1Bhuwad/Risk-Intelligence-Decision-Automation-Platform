"""
Tests for categorical and prefix audit.
"""

from src.audit.categorical import audit_categorical


def test_categorical_audit(synthetic_df, test_config):
    cat_df = audit_categorical(synthetic_df, test_config)
    assert len(cat_df) > 0
    assert "type" in cat_df["column"].values
    assert "nameOrig_PREFIX" in cat_df["column"].values
    assert "nameDest_PREFIX" in cat_df["column"].values

    # Check categories
    types_observed = set(cat_df[cat_df["column"] == "type"]["category"])
    assert "TRANSFER" in types_observed
    assert "PAYMENT" in types_observed

    # Check prefix observed
    orig_prefix_row = cat_df[cat_df["column"] == "nameOrig_PREFIX"].iloc[0]
    assert bool(orig_prefix_row["is_expected"]) is True
