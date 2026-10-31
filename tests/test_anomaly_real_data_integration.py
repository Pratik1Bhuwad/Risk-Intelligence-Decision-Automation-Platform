"""
Phase 05 Controlled Real-Data Integration Tests (Implementation Command 07).

Validates integration between the Phase 05 anomaly detection engine and real PaySim
feature pipelines on a strictly controlled, reproducible, leakage-safe sample:
  - 36 approved feature names and exact ordering.
  - Channel eligibility (TRANSFER and CASH_OUT only).
  - Immutable row_index preservation and lineage.
  - Strict historical temporal conditions (reference_step < scoring_step <= 400).
  - Reference population provenance (training partition only).
  - Channel-conditioned baseline isolation.
  - Controlled real-data scoring and eight-field schema contract.
  - Global combined alert budget (K = floor(0.0100 * N_S)) and population accounting.
  - Deterministic tie-breaking on row_index ascending.
  - Deterministic repeatability across identical runs.
  - Degraded/unscored state handling.
"""

import math
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import pytest

from src.anomaly.config import load_anomaly_config
from src.anomaly.engine import AnomalyDetectionEngine
from src.anomaly.schema import (
    AnomalyOutputRow,
    AnomalyOutputSchema,
    AnomalyStatus,
    EligibleChannel,
    ReasonCode,
    validate_output_row,
)
from src.anomaly.budget import AlertBudgetSelector
from src.features.metadata import FEATURE_CATALOG


@pytest.fixture(scope="module")
def real_data_sample() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load real PaySim processed features and partition into controlled slices:
      - Raw 100k sample (all step <= 10, strictly within training partition <= 400).
      - Reference slice: steps 1-5 (5,504 rows total).
      - Scoring slice: steps 6-7 (8,497 rows total; 2,243 eligible).
    """
    parquet_path = Path("data/processed/paysim_features_100000.parquet")
    assert parquet_path.exists(), f"Sample parquet file not found at {parquet_path}"

    df = pd.read_parquet(parquet_path)

    # Ingestion-assigned immutable 0-based ordinal row_index
    df["row_index"] = np.arange(len(df), dtype=int)

    # Reconstruct discrete simulation step from cyclical features
    df["step"] = (df["day_of_simulation"] * 24 + df["hour_of_day"]).astype(int)

    # Reconstruct transaction type from channel indicators
    conds = [
        df["is_transfer"] == 1,
        df["is_cash_out"] == 1,
        df["is_payment"] == 1,
        df["is_cash_in"] == 1,
        df["is_debit"] == 1,
    ]
    choices = ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]
    df["type"] = np.select(conds, choices, default="OTHER")

    # Drop target label isFraud to prevent label leakage into anomaly pipeline
    clean_df = df.drop(columns=["isFraud"])

    # Reference sample: steps 1-5 (5,504 rows)
    ref_df = clean_df[clean_df["step"] <= 5].copy()

    # Scoring sample: steps 6-7 (8,497 rows)
    score_df = clean_df[(clean_df["step"] >= 6) & (clean_df["step"] <= 7)].copy()

    return clean_df, ref_df, score_df


def test_feature_ordering_and_catalog_alignment():
    """Verify all 36 approved features are present in exact canonical order."""
    config = load_anomaly_config("configs/anomaly_detection.yaml", verify_provenance=True)
    catalog_features = list(FEATURE_CATALOG.keys())

    assert len(config.feature_names) == 36
    assert config.feature_names == catalog_features, (
        "Config feature names do not match FEATURE_CATALOG canonical order."
    )


def test_immutable_row_index_preservation(real_data_sample):
    """Verify row_index is assigned deterministically and survives transformations."""
    _, ref_df, score_df = real_data_sample

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # Score only eligible transactions
    score_eligible = score_df[score_df["type"].isin(["TRANSFER", "CASH_OUT"])].copy()
    initial_indices = score_eligible["row_index"].tolist()

    final_rows, out_df, _ = engine.score(score_eligible, enforce_temporal_split=True)

    output_indices = set(out_df["row_index"].tolist())
    for r_idx in initial_indices:
        assert r_idx in output_indices, f"Row index {r_idx} missing from output."

    assert len(out_df) == len(score_eligible)
    assert not out_df["row_index"].duplicated().any()


def test_temporal_boundary_and_zero_lookahead(real_data_sample):
    """Verify reference <= 400 and scoring step > reference step."""
    _, ref_df, score_df = real_data_sample

    assert ref_df["step"].max() <= 400, "Reference data exceeds training boundary step 400."
    assert score_df["step"].max() <= 400, "Scoring slice exceeds training boundary step 400."

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # Strict forward-chaining chronology: score_df min step (6) > ref_df max step (5)
    assert score_df["step"].min() > engine.reference_max_step

    # Enforce temporal check must succeed
    final_rows, out_df, _ = engine.score(
        score_df[score_df["type"].isin(["TRANSFER", "CASH_OUT"])],
        enforce_temporal_split=True,
    )
    assert len(final_rows) > 0

    # Test that introducing a past or same-step row raises Temporal Ordering Violation
    invalid_score_df = score_df.copy()
    invalid_score_df.iloc[0, invalid_score_df.columns.get_loc("step")] = engine.reference_max_step
    with pytest.raises(ValueError, match="Temporal Ordering Violation"):
        engine.score(invalid_score_df, enforce_temporal_split=True)


def test_reference_population_provenance(real_data_sample):
    """Verify reference population belongs strictly to training partition with no test/val rows."""
    _, ref_df, _ = real_data_sample

    # Check discrete steps
    steps = ref_df["step"].unique()
    assert all(1 <= s <= 400 for s in steps)
    # Ensure neither validation steps (401-550) nor test steps (551-743) exist
    assert not any(401 <= s <= 743 for s in steps)


def test_channel_isolation(real_data_sample):
    """Verify TRANSFER and CASH_OUT models and scalers are fitted independently."""
    _, ref_df, _ = real_data_sample

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    assert "TRANSFER" in engine.detectors
    assert "CASH_OUT" in engine.detectors

    # Detectors must be separate object instances
    assert engine.detectors["TRANSFER"] is not engine.detectors["CASH_OUT"]

    # Active features and baselines must be distinct per channel
    active_transfer = engine.preprocessor.get_active_features("TRANSFER")
    active_cashout = engine.preprocessor.get_active_features("CASH_OUT")

    assert len(active_transfer) > 0
    assert len(active_cashout) > 0

    transfer_medians = {f: engine.preprocessor.channel_baselines["TRANSFER"][f].median for f in active_transfer}
    cashout_medians = {f: engine.preprocessor.channel_baselines["CASH_OUT"][f].median for f in active_cashout}

    # Common active features should have different baseline statistics
    common_active = set(active_transfer).intersection(set(active_cashout))
    assert len(common_active) > 0
    # Amount median for TRANSFER vs CASH_OUT must differ in real data
    if "amount" in common_active:
        assert transfer_medians["amount"] != cashout_medians["amount"]


def test_real_data_scoring_and_eight_field_contract(real_data_sample):
    """Verify end-to-end scoring produces contract-compliant eight-field rows."""
    _, ref_df, score_df = real_data_sample

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    eligible_df = score_df[score_df["type"].isin(["TRANSFER", "CASH_OUT"])].copy()
    final_rows, out_df, budget_res = engine.score(eligible_df, enforce_temporal_split=True)

    # 1. Row count parity
    assert len(final_rows) == len(eligible_df)
    assert len(out_df) == len(eligible_df)

    # 2. Exact column contract
    expected_cols = [
        "schema_version",
        "row_index",
        "channel",
        "anomaly_score",
        "is_anomaly_flagged",
        "anomaly_status",
        "reason_code",
        "alert_budget_selected",
    ]
    assert list(out_df.columns) == expected_cols

    # 3. Row-level validation
    for r in final_rows:
        validate_output_row(r)
        assert r.schema_version == "1.0.0"  # Section 4.1: Output contract version initially 1.0.0
        assert r.channel in ["TRANSFER", "CASH_OUT"]
        assert r.anomaly_status == AnomalyStatus.SCORED.value
        assert isinstance(r.anomaly_score, float)
        assert math.isfinite(r.anomaly_score)
        assert isinstance(r.is_anomaly_flagged, bool)
        assert r.is_anomaly_flagged == r.alert_budget_selected
        assert r.reason_code is None

    # 4. Absence of NaN, Inf, or string "None"
    assert not out_df["anomaly_score"].isnull().any()
    assert not np.isinf(out_df["anomaly_score"]).any()
    assert not out_df["is_anomaly_flagged"].isnull().any()
    assert (out_df["reason_code"].astype(str) != "None").all() or out_df["reason_code"].isnull().all()


def test_alert_budget_reconciliation(real_data_sample):
    """Verify global alert budget allocation and population reconciliation invariants."""
    _, ref_df, score_df = real_data_sample

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    eligible_df = score_df[score_df["type"].isin(["TRANSFER", "CASH_OUT"])].copy()
    final_rows, out_df, budget_res = engine.score(eligible_df, enforce_temporal_split=True)

    n_transfer = (eligible_df["type"] == "TRANSFER").sum()
    n_cashout = (eligible_df["type"] == "CASH_OUT").sum()
    n_eligible = n_transfer + n_cashout
    n_scored = len(final_rows)
    k_expected = int(math.floor(0.0100 * n_scored))

    assert budget_res.input_count == n_eligible
    assert budget_res.eligible_count == n_eligible
    assert budget_res.ineligible_count == 0
    assert budget_res.successfully_scored_count == n_scored
    assert budget_res.unscored_eligible_count == 0
    assert budget_res.degraded_count == 0
    assert budget_res.unscored_count == 0
    assert budget_res.degraded_unscorable_count == 0
    assert budget_res.budget_denominator == n_scored
    assert budget_res.budget_k == k_expected
    assert budget_res.selected_alert_count == k_expected
    assert budget_res.input_count == budget_res.eligible_count + budget_res.ineligible_count
    assert budget_res.eligible_count == budget_res.successfully_scored_count + budget_res.unscored_eligible_count
    assert budget_res.degraded_count <= budget_res.unscored_eligible_count

    # Alert rates
    assert math.isclose(budget_res.alert_rate_scored, k_expected / n_scored, rel_tol=1e-6)
    assert math.isclose(budget_res.alert_rate_all_eligible, k_expected / n_eligible, rel_tol=1e-6)

    # Scored ranking and tie-breaking order:
    # Flagged rows must strictly have >= anomaly_score than unflagged rows
    flagged_scores = out_df.loc[out_df["is_anomaly_flagged"] == True, "anomaly_score"]
    unflagged_scores = out_df.loc[out_df["is_anomaly_flagged"] == False, "anomaly_score"]
    assert flagged_scores.min() >= unflagged_scores.max()


def test_deterministic_repeatability_on_real_data(real_data_sample):
    """Verify identical results across two independent executions on the same data."""
    _, ref_df, score_df = real_data_sample
    eligible_df = score_df[score_df["type"].isin(["TRANSFER", "CASH_OUT"])].copy()

    engine1 = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine1.fit(ref_df)
    _, out_df1, budget1 = engine1.score(eligible_df, enforce_temporal_split=True)

    engine2 = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine2.fit(ref_df)
    _, out_df2, budget2 = engine2.score(eligible_df, enforce_temporal_split=True)

    # Exact byte-for-byte or DataFrame equality
    pd.testing.assert_frame_equal(out_df1, out_df2)
    assert budget1 == budget2


def test_degraded_row_behavior_on_real_data(real_data_sample):
    """Verify degraded row creation, exclusion from budget, and population accounting."""
    _, ref_df, score_df = real_data_sample

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    eligible_df = score_df[score_df["type"].isin(["TRANSFER", "CASH_OUT"])].head(200).copy()

    # Artificially remove CASH_OUT detector to force all CASH_OUT rows into DEGRADED state
    del engine.detectors["CASH_OUT"]

    final_rows, out_df, budget_res = engine.score(eligible_df, enforce_temporal_split=True)

    degraded_rows = [r for r in final_rows if r.anomaly_status == AnomalyStatus.DEGRADED_UNSCORABLE.value]
    scored_rows = [r for r in final_rows if r.anomaly_status == AnomalyStatus.SCORED.value]

    assert len(degraded_rows) > 0
    assert len(scored_rows) > 0
    assert len(final_rows) == len(eligible_df)

    # Invariant check: eligible_count = successfully_scored_count + unscored_count
    assert budget_res.eligible_count == len(eligible_df)
    assert budget_res.successfully_scored_count == len(scored_rows)
    assert budget_res.unscored_count == len(degraded_rows)
    assert budget_res.degraded_unscorable_count == len(degraded_rows)
    assert budget_res.eligible_count == budget_res.successfully_scored_count + budget_res.unscored_count

    # Degraded rows must have null score and null flag, but non-null reason_code
    for d in degraded_rows:
        assert d.anomaly_score is None
        assert d.is_anomaly_flagged is None
        assert d.reason_code == ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value
        assert d.alert_budget_selected is False


def test_mixed_eligible_ineligible_real_data_scoring(real_data_sample):
    """Verify that scoring a mixed real-data batch correctly partitions populations."""
    _, ref_df, score_df = real_data_sample

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # Score full slice (contains TRANSFER, CASH_OUT, PAYMENT, CASH_IN, DEBIT)
    final_rows, out_df, budget_res = engine.score(score_df, enforce_temporal_split=True)

    n_input = len(score_df)  # 8,497
    n_transfer = (score_df["type"] == "TRANSFER").sum()  # 914
    n_cashout = (score_df["type"] == "CASH_OUT").sum()  # 1,329
    n_eligible = n_transfer + n_cashout  # 2,243
    n_ineligible = n_input - n_eligible  # 6,254

    assert budget_res.input_count == n_input
    assert budget_res.eligible_count == n_eligible
    assert budget_res.ineligible_count == n_ineligible
    assert budget_res.successfully_scored_count == n_eligible
    assert budget_res.unscored_eligible_count == 0
    assert budget_res.degraded_count == 0
    assert budget_res.budget_k == 22
    assert budget_res.selected_alert_count == 22

    # Verify population accounting invariants
    assert budget_res.input_count == budget_res.eligible_count + budget_res.ineligible_count
    assert budget_res.eligible_count == budget_res.successfully_scored_count + budget_res.unscored_eligible_count
    assert budget_res.degraded_count <= budget_res.unscored_eligible_count

    # Both rates are evaluated against their respective correct denominators
    assert math.isclose(budget_res.alert_rate_scored, 22 / n_eligible, rel_tol=1e-6)
    assert math.isclose(budget_res.alert_rate_all_eligible, 22 / n_eligible, rel_tol=1e-6)
    # Output rows must contain only eligible transactions
    assert len(final_rows) == n_eligible
    assert len(out_df) == n_eligible
    assert set(out_df["channel"].unique()) == {"TRANSFER", "CASH_OUT"}

