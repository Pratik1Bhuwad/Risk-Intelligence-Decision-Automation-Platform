"""
Dedicated Feature Leakage & Temporal Invariance Test Suite.

Verifies:
1. Complete absence of target and post-event fields.
2. Strict same-step exclusion (historical_step < current_step).
3. Non-self-contamination.
4. Future transaction invariance (step > step(T)).
5. Same-entity future modification invariance.
6. Cross-entity future modification invariance.
7. Pipeline determinism.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.policy import STRICTLY_EXCLUDED_FIELDS
from src.features.transformers import PointInTimeEntityVelocityTransformer
from src.features.pipeline import FeaturePipeline


@pytest.fixture
def base_temporal_df() -> pd.DataFrame:
    """
    Synthetic multi-step transaction dataset designed to test temporal boundaries.
    """
    return pd.DataFrame(
        {
            "step": [1, 1, 2, 2, 3, 4],
            "type": ["TRANSFER", "PAYMENT", "CASH_OUT", "TRANSFER", "TRANSFER", "PAYMENT"],
            "amount": [100.0, 50.0, 200.0, 300.0, 500.0, 75.0],
            "nameOrig": ["C_ORIG_1", "C_ORIG_2", "C_ORIG_1", "C_ORIG_3", "C_ORIG_1", "C_ORIG_4"],
            "oldbalanceOrg": [1000.0, 500.0, 900.0, 300.0, 700.0, 150.0],
            "newbalanceOrig": [900.0, 450.0, 700.0, 0.0, 200.0, 75.0],
            "nameDest": ["M_DEST_1", "C_DEST_2", "M_DEST_1", "C_DEST_2", "M_DEST_1", "C_DEST_3"],
            "oldbalanceDest": [0.0, 100.0, 0.0, 150.0, 0.0, 0.0],
            "newbalanceDest": [0.0, 150.0, 0.0, 450.0, 0.0, 0.0],
            "isFraud": [0, 0, 0, 1, 0, 0],
            "isFlaggedFraud": [0, 0, 0, 0, 0, 0],
        }
    )


def test_post_event_and_target_fields_absent_from_feature_matrix(base_temporal_df):
    """Verify that NO strictly excluded post-event or target field appears in features."""
    pipeline = FeaturePipeline()
    feature_df = pipeline.transform(base_temporal_df, include_target_label=False)

    feature_cols = set(feature_df.columns)
    forbidden_intersect = feature_cols.intersection(STRICTLY_EXCLUDED_FIELDS)

    assert len(forbidden_intersect) == 0, (
        f"Forbidden fields leaked into feature matrix: {forbidden_intersect}"
    )


def test_same_step_exclusion_policy(base_temporal_df):
    """
    Verify Correction 8: Same-step transactions must NOT enter prior history.
    At step 1: Row 0 and Row 1 are both at step 1.
    Neither Row 0 nor Row 1 should see any prior transaction (prior_tx_count must be 0).
    """
    tf = PointInTimeEntityVelocityTransformer()
    res = tf.transform(base_temporal_df)

    # Both row 0 and row 1 are at step 1
    assert res.loc[0, "dest_prior_tx_count"] == 0
    assert res.loc[1, "dest_prior_tx_count"] == 0
    assert res.loc[0, "orig_prior_tx_count"] == 0
    assert res.loc[1, "orig_prior_tx_count"] == 0

    assert res.loc[0, "dest_is_first_time_seen"] == 1
    assert res.loc[1, "dest_is_first_time_seen"] == 1


def test_strict_prior_temporal_boundary(base_temporal_df):
    """
    Verify Correction 5: At step S, only transactions with step < S are counted.
    Row 0: step=1, nameDest=M_DEST_1, amount=100
    Row 1: step=1, nameDest=C_DEST_2, amount=50
    Row 2: step=2, nameDest=M_DEST_1, amount=200
    Row 3: step=2, nameDest=C_DEST_2, amount=300
    Row 4: step=3, nameDest=M_DEST_1, amount=500
    """
    tf = PointInTimeEntityVelocityTransformer()
    res = tf.transform(base_temporal_df)

    # Row 2 (step 2, M_DEST_1): prior count should be 1 (from step 1), prior amount 100.0
    assert res.loc[2, "dest_prior_tx_count"] == 1
    assert res.loc[2, "dest_prior_total_amount"] == 100.0
    assert res.loc[2, "dest_time_since_last_tx"] == 1.0  # 2 - 1

    # Row 3 (step 2, C_DEST_2): prior count should be 1 (from step 1), prior amount 50.0
    # Note: Row 2 was also step 2, but Row 3 is at step 2, so Row 3 must NOT see Row 2!
    assert res.loc[3, "dest_prior_tx_count"] == 1
    assert res.loc[3, "dest_prior_total_amount"] == 50.0

    # Row 4 (step 3, M_DEST_1): sees step 1 (100) and step 2 (200). Prior count = 2, total = 300.0
    assert res.loc[4, "dest_prior_tx_count"] == 2
    assert res.loc[4, "dest_prior_total_amount"] == 300.0
    assert res.loc[4, "dest_time_since_last_tx"] == 1.0  # 3 - 2


def test_future_transaction_invariance(base_temporal_df):
    """
    Verify Correction 7: Modifying, adding, or removing future transactions (step > step(T))
    does NOT alter the features of T.
    """
    pipeline = FeaturePipeline()
    features_orig = pipeline.transform(base_temporal_df, include_target_label=False)

    # Transaction T is Row 2 (step = 2)
    t_features_before = features_orig.loc[2].copy()

    # Modify future transactions (Rows 4 and 5 at steps 3 and 4)
    modified_df = base_temporal_df.copy()
    modified_df.loc[4, "amount"] = 9999999.0
    modified_df.loc[5, "amount"] = 8888888.0
    modified_df.loc[4, "type"] = "CASH_IN"

    features_after = pipeline.transform(modified_df, include_target_label=False)
    t_features_after = features_after.loc[2]

    # Verify every single feature for Row 2 is identical
    for col in features_orig.columns:
        val_before = t_features_before[col]
        val_after = t_features_after[col]
        assert np.isclose(val_before, val_after, atol=1e-9), (
            f"Feature '{col}' changed for transaction T at step 2 when future was modified! "
            f"Before: {val_before}, After: {val_after}"
        )


def test_same_entity_future_invariance(base_temporal_df):
    """
    Verify Correction 6 (Scenario 1):
    Modify a future transaction belonging to the SAME entity as T.
    Verify that all features for T remain strictly unchanged.
    """
    pipeline = FeaturePipeline()
    features_orig = pipeline.transform(base_temporal_df, include_target_label=False)

    # Transaction T is Row 0 (step=1, dest=M_DEST_1, orig=C_ORIG_1)
    t0_features_before = features_orig.loc[0].copy()

    # Row 2 (step=2) and Row 4 (step=3) also belong to M_DEST_1 and C_ORIG_1!
    # Modify future transaction Row 4 (same entity M_DEST_1 / C_ORIG_1)
    modified_df = base_temporal_df.copy()
    modified_df.loc[4, "amount"] = 1234567.89
    modified_df.loc[4, "oldbalanceOrg"] = 99999.0

    features_after = pipeline.transform(modified_df, include_target_label=False)
    t0_features_after = features_after.loc[0]

    for col in features_orig.columns:
        assert np.isclose(t0_features_before[col], t0_features_after[col], atol=1e-9), (
            f"Same-entity future modification leak detected in feature '{col}'!"
        )


def test_cross_entity_future_invariance(base_temporal_df):
    """
    Verify Correction 6 (Scenario 2):
    Modify a future transaction belonging to a DIFFERENT entity from T.
    Verify that all features for T remain strictly unchanged.
    """
    pipeline = FeaturePipeline()
    features_orig = pipeline.transform(base_temporal_df, include_target_label=False)

    # Transaction T is Row 0 (step=1, dest=M_DEST_1, orig=C_ORIG_1)
    t0_features_before = features_orig.loc[0].copy()

    # Row 3 (step=2) belongs to DIFFERENT entity (C_DEST_2, C_ORIG_3)
    # Modify Row 3
    modified_df = base_temporal_df.copy()
    modified_df.loc[3, "amount"] = 888888.0
    modified_df.loc[3, "type"] = "DEBIT"

    features_after = pipeline.transform(modified_df, include_target_label=False)
    t0_features_after = features_after.loc[0]

    for col in features_orig.columns:
        assert np.isclose(t0_features_before[col], t0_features_after[col], atol=1e-9), (
            f"Cross-entity future modification leak detected in feature '{col}'!"
        )


def test_pipeline_determinism(base_temporal_df):
    """Verify that feature generation is 100% deterministic across multiple runs."""
    pipeline = FeaturePipeline()
    res1 = pipeline.transform(base_temporal_df, include_target_label=True)
    res2 = pipeline.transform(base_temporal_df, include_target_label=True)

    pd.testing.assert_frame_equal(res1, res2)
