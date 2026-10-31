"""
Comprehensive Edge-Case and Stress Tests for Phase 05 Anomaly Detection Engine.

Covers boundary conditions, edge cases, data validation, determinism, and leakage guards
under Specification v2.3.2 and the frozen configuration baseline.
"""

import math
import numpy as np
import pandas as pd
import pytest

from src.anomaly.engine import AnomalyDetectionEngine
from src.anomaly.schema import AnomalyOutputSchema, AnomalyStatus, ReasonCode
from src.anomaly.preprocessing import AnomalyPreprocessor
from src.anomaly.budget import AlertBudgetSelector
from src.features.metadata import FEATURE_CATALOG


def _make_dummy_row(row_index: int, channel: str = "TRANSFER", step: int = 10, val: float = 100.0) -> dict:
    """Create a single transaction dictionary containing row_index, type, step, and all 36 features."""
    row = {
        "row_index": int(row_index),
        "type": channel,
        "step": step,
    }
    for f in FEATURE_CATALOG.keys():
        if f.startswith("is_"):
            row[f] = 1 if f == f"is_{channel.lower()}" else 0
        else:
            row[f] = float(val)
    return row


def _make_dummy_dataset(n: int, channel: str = "TRANSFER", base_idx: int = 0, step: int = 10, spread: bool = True):
    """Create DataFrame with n rows and variance."""
    np.random.seed(base_idx + 100)
    rows = []
    for i in range(n):
        val = 10.0 + (float(i * 5.0) if spread else 0.0)
        rows.append(_make_dummy_row(base_idx + i, channel=channel, step=step, val=val))
    return pd.DataFrame(rows)


def test_edge_case_empty_input():
    """Verify engine behavior when input DataFrame has 0 rows."""
    ref_df = _make_dummy_dataset(50, "TRANSFER", base_idx=0)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    empty_df = pd.DataFrame(columns=["row_index", "type"] + list(FEATURE_CATALOG.keys()))
    rows, out_df, summary = engine.score(empty_df)

    assert len(rows) == 0
    assert len(out_df) == 0
    assert list(out_df.columns) == AnomalyOutputSchema.COLUMN_NAMES
    assert summary.successfully_scored_count == 0
    assert summary.status == "NOT_EVALUABLE"


def test_edge_case_empty_eligible_population():
    """Verify behavior when input contains only ineligible channels (e.g. PAYMENT, DEBIT)."""
    ref_df = _make_dummy_dataset(50, "TRANSFER", base_idx=0)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # 10 PAYMENT rows only
    pay_df = _make_dummy_dataset(10, "PAYMENT", base_idx=100)
    rows, out_df, summary = engine.score(pay_df)

    assert summary.input_count == 10
    assert summary.eligible_count == 0
    assert summary.ineligible_count == 10
    assert summary.successfully_scored_count == 0
    assert summary.unscored_eligible_count == 0
    assert summary.degraded_count == 0
    assert summary.status == "NOT_EVALUABLE"
    assert summary.alert_rate_scored is None
    assert summary.alert_rate_all_eligible is None
    assert summary.input_count == summary.eligible_count + summary.ineligible_count
    assert summary.eligible_count == summary.successfully_scored_count + summary.unscored_eligible_count


def test_edge_case_single_eligible_row():
    """Verify behavior when exactly one eligible transaction is scored."""
    ref_df = _make_dummy_dataset(50, "TRANSFER", base_idx=0)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    single_df = _make_dummy_dataset(1, "TRANSFER", base_idx=100)
    rows, out_df, summary = engine.score(single_df)

    assert len(rows) == 1
    assert summary.successfully_scored_count == 1
    # K = floor(0.0100 * 1) = 0
    assert summary.budget_k == 0
    assert summary.selected_alert_count == 0
    assert rows[0].is_anomaly_flagged is False
    assert rows[0].alert_budget_selected is False
    assert rows[0].anomaly_status == AnomalyStatus.SCORED.value


def test_edge_case_missing_feature_column():
    """Verify that omitting any of the 36 canonical features raises ValueError."""
    prep = AnomalyPreprocessor()
    df = _make_dummy_dataset(10, "TRANSFER")
    # Drop one required feature
    df_missing = df.drop(columns=["amount"])
    with pytest.raises(ValueError, match="Missing required anomaly feature columns"):
        prep.validate_inputs(df_missing)


def test_edge_case_nan_and_inf_detection():
    """Verify that NaN or Inf values in input features are rejected."""
    prep = AnomalyPreprocessor()
    df_nan = _make_dummy_dataset(10, "TRANSFER")
    df_nan.loc[2, "amount"] = np.nan
    with pytest.raises(ValueError, match="NaN/null values"):
        prep.validate_inputs(df_nan)

    df_inf = _make_dummy_dataset(10, "TRANSFER")
    df_inf.loc[3, "amount"] = np.inf
    with pytest.raises(ValueError, match="infinite values"):
        prep.validate_inputs(df_inf)


def test_edge_case_duplicate_row_index():
    """Verify rejection of duplicate row_index values in scoring batch."""
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    ref_df = _make_dummy_dataset(50, "TRANSFER", base_idx=0)
    engine.fit(ref_df)

    # Batch with duplicate row_index 99
    r1 = _make_dummy_row(99, "TRANSFER")
    r2 = _make_dummy_row(99, "TRANSFER")
    bad_df = pd.DataFrame([r1, r2])

    with pytest.raises(ValueError, match="duplicate 'row_index' values"):
        engine.score(bad_df)


def test_edge_case_order_invariance_of_alert_selection():
    """
    Verify that permuting input row ordering produces the exact same alert selection set.
    Tests Specification v2.3.1 Section 2.2 & v2.3.2 Section 3.
    """
    ref_transfer = _make_dummy_dataset(100, "TRANSFER", base_idx=0)
    ref_cash_out = _make_dummy_dataset(100, "CASH_OUT", base_idx=100)
    ref_df = pd.concat([ref_transfer, ref_cash_out], ignore_index=True)

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # 200 test rows -> K = floor(0.0100 * 200) = 2 alerts
    test_df_original = _make_dummy_dataset(200, "TRANSFER", base_idx=200)
    # Give two rows extreme values to be top anomalies
    test_df_original.loc[45, "amount"] = 99999999.0
    test_df_original.loc[120, "amount"] = 88888888.0

    # Permuted version of the exact same records
    shuffled_idx = np.random.RandomState(42).permutation(len(test_df_original))
    test_df_permuted = test_df_original.iloc[shuffled_idx].copy()

    _, out1, sum1 = engine.score(test_df_original)
    _, out2, sum2 = engine.score(test_df_permuted)

    # Both must select the exact same alert count
    assert sum1.selected_alert_count == sum2.selected_alert_count == 2

    alerts1 = set(out1[out1["alert_budget_selected"] == True]["row_index"])
    alerts2 = set(out2[out2["alert_budget_selected"] == True]["row_index"])

    assert alerts1 == alerts2, f"Order permutation changed alert set! {alerts1} != {alerts2}"


def test_edge_case_repeated_scoring_runs_bitwise_identity():
    """Verify that repeated scoring runs on identical inputs yield bitwise identical scores."""
    ref_df = _make_dummy_dataset(60, "TRANSFER", base_idx=0)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    test_df = _make_dummy_dataset(40, "TRANSFER", base_idx=100)
    _, out1, _ = engine.score(test_df)
    _, out2, _ = engine.score(test_df)

    np.testing.assert_array_equal(out1["anomaly_score"].to_numpy(), out2["anomaly_score"].to_numpy())
    np.testing.assert_array_equal(out1["alert_budget_selected"].to_numpy(), out2["alert_budget_selected"].to_numpy())


def test_edge_case_constant_reference_features():
    """Verify that constant reference features are cleanly excluded without crashing."""
    rows = []
    for i in range(50):
        r = _make_dummy_row(i, "TRANSFER", val=5.0)  # Constant value 5.0 for all features!
        rows.append(r)
    ref_df = pd.DataFrame(rows)

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # Active features must be empty
    assert len(engine.preprocessor.get_active_features("TRANSFER")) == 0

    # Scoring must degrade safely to State C
    test_df = pd.DataFrame([_make_dummy_row(100, "TRANSFER", val=5.0)])
    rows_out, out_df, summary = engine.score(test_df)

    assert len(rows_out) == 1
    assert rows_out[0].anomaly_status == AnomalyStatus.DEGRADED_UNSCORABLE.value
    assert rows_out[0].reason_code == ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value
    assert rows_out[0].anomaly_score is None


def test_edge_case_insufficient_positive_samples():
    """Verify that positive-subset fallback excludes feature when positive sample count < 10."""
    # 90 zeros and only 5 positive values (MAD=0, IQR=0, pos_obs = 5 < 10)
    zeros = [0.0] * 90
    positives = [1.0, 2.0, 3.0, 4.0, 5.0]
    data = np.array(zeros + positives)

    res = AnomalyPreprocessor.compute_feature_dispersion(data, "amount", "TRANSFER", min_pos_obs=10)
    assert res.method == "EXCLUDED"
    assert res.is_active is False
    assert res.scale is None
    assert "INSUFFICIENT_POSITIVE_OBSERVATIONS_5_LT_10" in res.exclusion_reason


def test_edge_case_temporal_leakage_in_fit_rejected():
    """Verify that reference data containing future simulation steps (>400) is rejected."""
    # Data with step 450 (> train_max_step 400)
    ref_future = _make_dummy_dataset(30, "TRANSFER", base_idx=0, step=450)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    with pytest.raises(ValueError, match="Temporal Leakage Violation: reference data contains step 450 exceeding train_max_step"):
        engine.fit(ref_future)


def test_edge_case_temporal_ordering_violation_in_score_rejected():
    """Verify that scoring data containing step <= reference_max_step is rejected when temporal split enforced."""
    ref_df = _make_dummy_dataset(30, "TRANSFER", base_idx=0, step=300)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # Scoring batch with step 250 (<= reference_max_step 300)
    score_past_df = _make_dummy_dataset(20, "TRANSFER", base_idx=100, step=250)
    with pytest.raises(ValueError, match="Temporal Ordering Violation"):
        engine.score(score_past_df, enforce_temporal_split=True)

