"""
Unit tests for Anomaly Preprocessing and the Four-Tier Fallback Hierarchy.
"""

import numpy as np
import pandas as pd
import pytest

from src.anomaly.preprocessing import (
    AnomalyPreprocessor,
    FeatureFallbackResult,
    MAD_SCALE_FACTOR,
    IQR_DIVISOR,
)
from src.features.metadata import FEATURE_CATALOG


def test_fallback_tier_1_mad():
    """Verify primary Tier 1 MAD scaling when dispersion is non-zero."""
    data = np.array([10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
    res = AnomalyPreprocessor.compute_feature_dispersion(data, "amount", "TRANSFER")
    assert res.method == "MAD"
    assert res.is_active is True
    assert res.scale is not None and res.scale > 0.0
    expected_mad = np.median(np.abs(data - np.median(data)))
    assert np.isclose(res.scale, expected_mad * MAD_SCALE_FACTOR)


def test_fallback_tier_2_iqr():
    """Verify Tier 2 IQR fallback when MAD is 0 but IQR > 0."""
    # More than 50% identical values -> MAD = 0, but 75th percentile is higher
    data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 20.0])
    med = np.median(data)  # 0.0
    assert np.median(np.abs(data - med)) == 0.0  # MAD is zero

    res = AnomalyPreprocessor.compute_feature_dispersion(data, "amount", "TRANSFER")
    assert res.method == "IQR"
    assert res.is_active is True
    assert res.scale is not None and res.scale > 0.0
    q75, q25 = np.percentile(data, [75, 25])
    assert np.isclose(res.scale, (q75 - q25) / IQR_DIVISOR)


def test_fallback_tier_3_positive_subset():
    """Verify Tier 3 Positive-Subset Dispersion when MAD=0 and IQR=0, but >=10 positive samples exist."""
    # 80 zeros, and 12 varying positive values (MAD=0, IQR=0)
    zeros = [0.0] * 80
    positives = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    data = np.array(zeros + positives)
    assert np.median(np.abs(data - np.median(data))) == 0.0
    q75, q25 = np.percentile(data, [75, 25])
    assert q75 - q25 == 0.0

    res = AnomalyPreprocessor.compute_feature_dispersion(data, "dest_prior_tx_count", "TRANSFER", min_pos_obs=10)
    assert res.method == "positive_subset_dispersion"
    assert res.is_active is True
    assert res.scale is not None and res.scale > 0.0
    assert np.isclose(res.scale, np.std(positives, ddof=1))


def test_fallback_tier_4_feature_exclusion_no_epsilon():
    """Verify Tier 4 Feature Exclusion when all dispersion methods fail. Prohibits epsilon."""
    # Invariant feature (e.g. constant 0.0 or constant 1.0)
    data = np.array([1.0] * 100)
    res = AnomalyPreprocessor.compute_feature_dispersion(data, "is_transfer", "TRANSFER", min_pos_obs=10)
    assert res.method == "EXCLUDED"
    assert res.is_active is False
    assert res.scale is None  # Never an arbitrary epsilon like 1e-6!
    assert res.exclusion_reason is not None


def test_zero_leakage_enforcement():
    """Verify that prohibited post-event fields are strictly rejected."""
    prep = AnomalyPreprocessor()
    df_leakage = pd.DataFrame({
        "row_index": [0],
        "type": ["TRANSFER"],
        "newbalanceOrig": [100.0],  # Strictly prohibited post-event field!
    })
    with pytest.raises(ValueError, match="Prediction Security Violation: Input contains prohibited fields"):
        prep.validate_inputs(df_leakage)


def test_row_index_validation():
    """Verify that duplicate or missing row_index values are rejected."""
    prep = AnomalyPreprocessor()
    # Missing row_index
    df_missing = pd.DataFrame({"type": ["TRANSFER"], "amount": [100.0]})
    with pytest.raises(ValueError, match="Missing required immutable 'row_index'"):
        prep.validate_inputs(df_missing, require_row_index=True)

    # Duplicate row_index
    df_dup = pd.DataFrame({
        "row_index": [1, 1],  # Duplicate!
        "type": ["TRANSFER", "TRANSFER"],
    })
    for f in FEATURE_CATALOG.keys():
        df_dup[f] = 0.0
    with pytest.raises(ValueError, match="duplicate 'row_index' values"):
        prep.validate_inputs(df_dup, require_row_index=True)


def test_channel_conditioned_fitting():
    """Verify separate robust baselines for TRANSFER and CASH_OUT."""
    n = 50
    rows = []
    for i in range(n):
        rows.append({"type": "TRANSFER", "amount": float(i * 100)})
        rows.append({"type": "CASH_OUT", "amount": float(i * 500)})

    df = pd.DataFrame(rows)
    for f in FEATURE_CATALOG.keys():
        if f not in df.columns:
            df[f] = 1.0

    prep = AnomalyPreprocessor()
    prep.fit(df)

    t_res = prep.channel_baselines["TRANSFER"]["amount"]
    c_res = prep.channel_baselines["CASH_OUT"]["amount"]

    assert t_res.is_active and c_res.is_active
    assert t_res.median != c_res.median  # Channel conditioned!
    assert t_res.scale != c_res.scale

