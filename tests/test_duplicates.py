"""
Tests for duplicate audit module.
"""

from src.audit.duplicates import audit_duplicates


def test_duplicates_detection(synthetic_df, test_config):
    dup_df = audit_duplicates(synthetic_df, test_config)
    assert len(dup_df) >= 3

    exact_row = dup_df[dup_df["check_type"] == "EXACT_DUPLICATE_ROWS"].iloc[0]
    assert exact_row["duplicate_records"] == 0

    # In synthetic fixture, nameOrig C10001 appears twice
    orig_row = dup_df[dup_df["target_columns"] == "nameOrig"].iloc[0]
    assert orig_row["duplicate_records"] == 1
    assert bool(orig_row["is_explicit_id"]) is False


def test_exact_duplicates_present(synthetic_df, test_config):
    import pandas as pd

    # Append duplicate row
    df_with_dups = pd.concat(
        [synthetic_df, synthetic_df.iloc[[0]]], ignore_index=True
    )
    dup_df = audit_duplicates(df_with_dups, test_config)
    exact_row = dup_df[dup_df["check_type"] == "EXACT_DUPLICATE_ROWS"].iloc[0]
    assert exact_row["duplicate_records"] == 1
