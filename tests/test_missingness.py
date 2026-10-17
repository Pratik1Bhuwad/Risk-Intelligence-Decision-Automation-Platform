"""
Tests for missing-value audit module.
"""

import numpy as np
import pandas as pd
from src.audit.missingness import audit_missingness


def test_missingness_detection(synthetic_df, test_config):
    df_with_missing = synthetic_df.copy()
    # Inject NaN, blank, whitespace, text marker, and zeros
    df_with_missing.loc[0, "type"] = np.nan
    df_with_missing.loc[1, "nameOrig"] = ""
    df_with_missing.loc[2, "nameDest"] = "   "
    df_with_missing.loc[3, "type"] = "null"

    missing_df, stratified_df = audit_missingness(df_with_missing, test_config)
    assert len(missing_df) == 11

    # Check type column
    type_row = missing_df[missing_df["column"] == "type"].iloc[0]
    assert type_row["nan_count"] == 1
    assert type_row["text_marker_count"] == 1
    assert type_row["total_missing_count"] == 2

    # Check nameOrig blank count
    orig_row = missing_df[missing_df["column"] == "nameOrig"].iloc[0]
    assert orig_row["blank_count"] == 1

    # Check nameDest whitespace count
    dest_row = missing_df[missing_df["column"] == "nameDest"].iloc[0]
    assert dest_row["whitespace_count"] == 1

    # Check zero count in oldbalanceDest
    obd_row = missing_df[missing_df["column"] == "oldbalanceDest"].iloc[0]
    assert obd_row["zero_count"] > 0
