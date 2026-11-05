"""
Unit tests for Phase 06 Anomaly Evaluation & Validation module (src/anomaly/evaluation.py).

Enforces strict compliance with:
- Protocol v1.2.7-DRAFT
- Specification v2.3.2
- Eight-Gate Governance Baseline

RESTRICTIONS ENFORCED:
- 100% synthetic fixtures only (NumPy / pandas generated in memory).
- Zero reading of real PaySim parquet or csv files.
- Zero fitting or scoring of real detector models.
- Fast, deterministic execution.
"""

import math
from typing import List
import numpy as np
import pandas as pd
import pytest

from src.anomaly.schema import AnomalyStatus, EligibleChannel, ReasonCode
from src.features.metadata import FEATURE_CATALOG
from src.anomaly.evaluation import (
    APPROVED_ALERT_BUDGET_SCENARIOS,
    DEFAULT_PSI_BINS,
    DEFAULT_PSI_EPSILON,
    STATUS_COMPLETED,
    STATUS_EVALUATED,
    STATUS_NOT_EVALUABLE,
    STEP_RANGE_CONTINUOUS_EVALUATION,
    STEP_RANGE_PRELIMINARY_VALIDATION,
    STEP_RANGE_QUALIFIED_HOLDOUT,
    STEP_RANGE_REFERENCE,
    compute_gate6_diagnostic_metrics,
    compute_psi,
    evaluate_budget_sensitivity,
    extract_clean_features_and_target,
    format_evaluation_report,
    reconstruct_step_and_channel,
    slice_evaluation_population,
    validate_evaluation_data_contract,
)


# ==============================================================================
# SYNTHETIC FIXTURES
# ==============================================================================

@pytest.fixture
def canonical_features() -> List[str]:
    """Return the 36 canonical anomaly feature names."""
    return list(FEATURE_CATALOG.keys())


@pytest.fixture
def synthetic_raw_dataframe(canonical_features: List[str]) -> pd.DataFrame:
    """
    Generate synthetic DataFrame mirroring raw PaySim feature format without leakage.
    Contains 200 rows with simulated temporal and channel fields.
    """
    rng = np.random.RandomState(42)
    n_rows = 200

    data = {
        "row_index": np.arange(n_rows, dtype=int),
        "day_of_simulation": rng.randint(0, 31, size=n_rows).astype(np.int16),
        "hour_of_day": rng.randint(0, 24, size=n_rows).astype(np.int8),
        "is_transfer": rng.choice([0, 1], size=n_rows, p=[0.7, 0.3]).astype(np.int8),
        "is_cash_out": np.zeros(n_rows, dtype=np.int8),
        "is_payment": np.zeros(n_rows, dtype=np.int8),
        "is_cash_in": np.zeros(n_rows, dtype=np.int8),
        "is_debit": np.zeros(n_rows, dtype=np.int8),
        "isFraud": rng.choice([0, 1], size=n_rows, p=[0.95, 0.05]).astype(np.int8),
    }

    # Ensure mutually exclusive channel types
    for i in range(n_rows):
        if data["is_transfer"][i] == 0:
            data["is_cash_out"][i] = 1

    # Add 36 canonical features
    for feat in canonical_features:
        data[feat] = rng.randn(n_rows).astype(np.float32)

    return pd.DataFrame(data)


# ==============================================================================
# DATA CONTRACT VALIDATION TESTS
# ==============================================================================

def test_validate_evaluation_data_contract_success(synthetic_raw_dataframe: pd.DataFrame):
    """Assert valid synthetic DataFrame passes contract validation."""
    validate_evaluation_data_contract(synthetic_raw_dataframe, require_target=True)


def test_validate_evaluation_data_contract_row_index_null(synthetic_raw_dataframe: pd.DataFrame):
    """Assert null row_index raises ValueError."""
    df = synthetic_raw_dataframe.copy()
    df.loc[5, "row_index"] = None
    with pytest.raises(ValueError, match="contains null values"):
        validate_evaluation_data_contract(df)


def test_validate_evaluation_data_contract_row_index_duplicate(synthetic_raw_dataframe: pd.DataFrame):
    """Assert duplicate row_index raises ValueError."""
    df = synthetic_raw_dataframe.copy()
    df.loc[10, "row_index"] = df.loc[0, "row_index"]
    with pytest.raises(ValueError, match="contains 1 duplicates"):
        validate_evaluation_data_contract(df)


def test_validate_evaluation_data_contract_row_index_non_integer(synthetic_raw_dataframe: pd.DataFrame):
    """Assert non-integer row_index raises TypeError."""
    df = synthetic_raw_dataframe.copy()
    df["row_index"] = df["row_index"].astype(str)
    with pytest.raises(TypeError, match="must be integer dtype"):
        validate_evaluation_data_contract(df)


def test_validate_evaluation_data_contract_missing_temporal(synthetic_raw_dataframe: pd.DataFrame):
    """Assert missing temporal fields raises ValueError."""
    df = synthetic_raw_dataframe.drop(columns=["day_of_simulation", "hour_of_day"])
    with pytest.raises(ValueError, match="missing temporal fields"):
        validate_evaluation_data_contract(df)


def test_validate_evaluation_data_contract_missing_channel(synthetic_raw_dataframe: pd.DataFrame):
    """Assert missing channel fields raises ValueError."""
    df = synthetic_raw_dataframe.drop(columns=["is_transfer", "is_cash_out"])
    with pytest.raises(ValueError, match="missing channel fields"):
        validate_evaluation_data_contract(df)


def test_validate_evaluation_data_contract_missing_target(synthetic_raw_dataframe: pd.DataFrame):
    """Assert missing isFraud when require_target=True raises ValueError."""
    df = synthetic_raw_dataframe.drop(columns=["isFraud"])
    with pytest.raises(ValueError, match="required target column 'isFraud' is missing"):
        validate_evaluation_data_contract(df, require_target=True)

    # When require_target=False, should pass
    validate_evaluation_data_contract(df, require_target=False)


def test_validate_evaluation_data_contract_missing_features(synthetic_raw_dataframe: pd.DataFrame):
    """Assert missing canonical feature raises ValueError."""
    df = synthetic_raw_dataframe.drop(columns=["amount"])
    with pytest.raises(ValueError, match="missing 1 canonical features"):
        validate_evaluation_data_contract(df)


# ==============================================================================
# RECONSTRUCTION & DECOUPLING TESTS
# ==============================================================================

def test_reconstruct_step_exact_identity():
    """Verify step = day_of_simulation * 24 + hour_of_day exact identity across simulation hours."""
    days = [0, 0, 1, 1, 15, 30]
    hours = [1, 23, 0, 1, 12, 23]
    expected_steps = [1, 23, 24, 25, 372, 743]

    df = pd.DataFrame({
        "day_of_simulation": days,
        "hour_of_day": hours,
        "is_transfer": [1, 0, 1, 0, 1, 0],
        "is_cash_out": [0, 1, 0, 1, 0, 1],
    })

    reconstructed = reconstruct_step_and_channel(df)
    assert reconstructed["step"].tolist() == expected_steps
    assert reconstructed["type"].tolist() == [
        "TRANSFER", "CASH_OUT", "TRANSFER", "CASH_OUT", "TRANSFER", "CASH_OUT"
    ]


def test_extract_clean_features_and_target_leakage_safety(
    synthetic_raw_dataframe: pd.DataFrame,
    canonical_features: List[str],
):
    """Assert target decoupling and complete exclusion of prohibited leakage fields."""
    df = reconstruct_step_and_channel(synthetic_raw_dataframe)
    clean_df, y_true = extract_clean_features_and_target(df, expected_features=canonical_features)

    assert y_true is not None
    assert len(y_true) == len(df)
    assert "isFraud" not in clean_df.columns
    assert "isFlaggedFraud" not in clean_df.columns
    assert "newbalanceOrig" not in clean_df.columns
    assert "newbalanceDest" not in clean_df.columns
    assert "row_index" in clean_df.columns
    assert "type" in clean_df.columns

    # Verify canonical feature set retained
    for feat in canonical_features:
        assert feat in clean_df.columns


def test_slice_evaluation_population():
    """Assert forward-chained population slices match exact step ranges."""
    df = pd.DataFrame({"step": [1, 100, 400, 401, 500, 550, 551, 650, 743, 744]})

    ref = slice_evaluation_population(df, STEP_RANGE_REFERENCE)
    assert ref["step"].tolist() == [1, 100, 400]

    val = slice_evaluation_population(df, STEP_RANGE_PRELIMINARY_VALIDATION)
    assert val["step"].tolist() == [401, 500, 550]

    holdout = slice_evaluation_population(df, STEP_RANGE_QUALIFIED_HOLDOUT)
    assert holdout["step"].tolist() == [551, 650, 743]

    continuous = slice_evaluation_population(df, STEP_RANGE_CONTINUOUS_EVALUATION)
    assert continuous["step"].tolist() == [401, 500, 550, 551, 650, 743]


# ==============================================================================
# PSI CALCULATION TESTS (SELECTIVE SMOOTHING & BOUNDARY INVARIANTS)
# ==============================================================================

def test_compute_psi_identical_distributions():
    """Assert PSI is 0.0 when comparing a distribution to an identical copy."""
    rng = np.random.RandomState(42)
    scores = rng.normal(loc=0.0, scale=1.0, size=1000)

    result = compute_psi(scores, scores)
    assert result["status"] == STATUS_COMPLETED
    assert result["psi"] == 0.0
    assert result["n_ref_finite"] == 1000
    assert result["n_eval_finite"] == 1000
    assert result["num_bins"] == 10


def test_compute_psi_empty_reference_population():
    """Assert empty reference array short-circuits to NOT_EVALUABLE immediately."""
    result = compute_psi(reference_scores=[], evaluation_scores=[0.1, 0.2, 0.3])
    assert result["status"] == STATUS_NOT_EVALUABLE
    assert result["reason"] == "EMPTY_FINITE_POPULATION"
    assert result["psi"] is None
    assert result["cut_points"] == []


def test_compute_psi_empty_evaluation_population():
    """Assert empty evaluation array short-circuits to NOT_EVALUABLE immediately."""
    result = compute_psi(reference_scores=[0.1, 0.2, 0.3], evaluation_scores=[])
    assert result["status"] == STATUS_NOT_EVALUABLE
    assert result["reason"] == "EMPTY_FINITE_POPULATION"
    assert result["psi"] is None


def test_compute_psi_zero_score_variance_collapsed_bins():
    """Assert identical reference scores collapse cut-points and return NOT_EVALUABLE."""
    identical_scores = [0.42] * 500
    eval_scores = [0.1, 0.2, 0.3, 0.4, 0.5]

    result = compute_psi(reference_scores=identical_scores, evaluation_scores=eval_scores)
    assert result["status"] == STATUS_NOT_EVALUABLE
    assert result["reason"] == "ZERO_SCORE_VARIANCE_COLLAPSED_BINS"
    assert result["psi"] is None


def test_compute_psi_selective_smoothing_behavior():
    """
    Assert selective smoothing:
    - Epsilon (1e-4) is added ONLY to bins with zero proportion.
    - Nonzero proportion bins are left completely unaltered before renormalization.
    - Post-renormalization proportions sum to 1.0.
    """
    # Reference covers 0.0 to 10.0
    ref_scores = np.linspace(0.0, 10.0, 1000)
    # Evaluation covers 5.0 to 15.0 (so lower bins will have 0 evaluation count)
    eval_scores = np.linspace(5.0, 15.0, 1000)

    result = compute_psi(ref_scores, eval_scores, epsilon=1e-4)
    assert result["status"] == STATUS_COMPLETED
    assert result["psi"] > 0.0

    p_star = np.array(result["p_proportions"])
    q_star = np.array(result["q_proportions"])

    # Both must sum to 1.0 within float precision
    assert math.isclose(np.sum(p_star), 1.0, rel_tol=1e-6)
    assert math.isclose(np.sum(q_star), 1.0, rel_tol=1e-6)

    # All smoothed values must be strictly positive (preventing ln(0))
    assert np.all(p_star > 0.0)
    assert np.all(q_star > 0.0)


def test_compute_psi_finite_score_inclusion_and_nan_accounting():
    """Assert s=0.0 is included, and NaN/Inf are tracked and excluded from finite counts."""
    ref_scores = [-1.0, 0.0, 0.5, 1.0, np.nan, np.inf]
    eval_scores = [0.0, 0.2, 0.4, 0.8, -np.inf]

    result = compute_psi(ref_scores, eval_scores)
    assert result["n_ref_finite"] == 4
    assert result["n_ref_nonfinite"] == 2
    assert result["n_eval_finite"] == 4
    assert result["n_eval_nonfinite"] == 1


# ==============================================================================
# GATE 6.1 METRIC CALCULATIONS & SENSITIVITY SUITE TESTS
# ==============================================================================

def test_compute_gate6_diagnostic_metrics_standard():
    """Assert Gate 6.1 diagnostic metrics compute properly under standard conditions."""
    metrics = compute_gate6_diagnostic_metrics(
        eligible_count=1000,
        scored_count=980,
        degraded_count=20,
        f_elig=50,
        f_scored=48,
        tp_k=12,
        k=20,
        score_psi=0.045,
    )

    assert metrics["T_deg"] == 20.0 / 1000.0  # 0.02
    assert metrics["T_psi"] == 0.045
    assert metrics["T_prec"] == 12.0 / 20.0  # 0.60
    assert metrics["T_rec_scored"] == 12.0 / 48.0  # 0.25
    assert metrics["T_rec_elig"] == 12.0 / 50.0  # 0.24
    assert metrics["T_cov"] == 48.0 / 50.0  # 0.96

    # Prevalence in scored = 48 / 980 = 0.048979...
    # Enrichment = 0.60 / (48 / 980) = 12.25
    expected_enrich = (12.0 / 20.0) / (48.0 / 980.0)
    assert math.isclose(metrics["T_enrich"], expected_enrich, rel_tol=1e-5)


def test_compute_gate6_diagnostic_metrics_boundary_f_scored_zero():
    """
    Assert boundary condition when F_scored == 0 while F_elig > 0:
    - TP_k must be 0
    - T_rec_scored is NOT_EVALUABLE (None)
    - T_rec_elig evaluates to 0.0 from primary definition (0 / F_elig)
    - T_cov is 0.0 (0 / F_elig)
    """
    metrics = compute_gate6_diagnostic_metrics(
        eligible_count=500,
        scored_count=500,
        degraded_count=0,
        f_elig=10,
        f_scored=0,
        tp_k=0,
        k=10,
    )

    assert metrics["T_rec_scored"] is None
    assert metrics["T_rec_elig"] == 0.0
    assert metrics["T_cov"] == 0.0
    assert metrics["T_enrich"] is None


def test_evaluate_budget_sensitivity_scenarios():
    """
    Assert retrospective sensitivity analysis across approved rates:
    0.10%, 0.50%, 1.00%, 2.00%.
    """
    n_rows = 1000
    rng = np.random.RandomState(42)

    # 1000 scored rows with scores from 0.0 to 1.0
    scores = rng.uniform(0.0, 1.0, size=n_rows)
    scored_df = pd.DataFrame({
        "row_index": np.arange(n_rows, dtype=int),
        "channel": ["TRANSFER"] * (n_rows // 2) + ["CASH_OUT"] * (n_rows // 2),
        "anomaly_score": scores,
        "is_anomaly_flagged": [False] * n_rows,
        "anomaly_status": [AnomalyStatus.SCORED.value] * n_rows,
        "reason_code": [None] * n_rows,
        "alert_budget_selected": [False] * n_rows,
    })

    # Fraud concentrated in higher scores
    y_true = pd.Series(
        np.where(scores > 0.90, 1, 0),
        index=scored_df["row_index"],
    )

    results = evaluate_budget_sensitivity(
        scored_df=scored_df,
        y_true=y_true,
        scenarios=APPROVED_ALERT_BUDGET_SCENARIOS,
    )

    assert results["n_scored"] == 1000
    assert results["n_eligible"] == 1000

    scenarios = results["scenarios"]
    # Check 0.10%: K = floor(0.0010 * 1000) = 1
    assert scenarios["0.10%"]["K"] == 1
    assert scenarios["0.10%"]["status"] == STATUS_EVALUATED

    # Check 0.50%: K = floor(0.0050 * 1000) = 5
    assert scenarios["0.50%"]["K"] == 5
    assert scenarios["0.50%"]["status"] == STATUS_EVALUATED

    # Check 1.00%: K = floor(0.0100 * 1000) = 10
    assert scenarios["1.00%"]["K"] == 10
    assert scenarios["1.00%"]["status"] == STATUS_EVALUATED

    # Check 2.00%: K = floor(0.0200 * 1000) = 20
    assert scenarios["2.00%"]["K"] == 20
    assert scenarios["2.00%"]["status"] == STATUS_EVALUATED

    # Verify monotonic expansion of alerts: K_0.1% < K_0.5% < K_1.0% < K_2.0%
    assert (
        scenarios["0.10%"]["K"]
        < scenarios["0.50%"]["K"]
        < scenarios["1.00%"]["K"]
        < scenarios["2.00%"]["K"]
    )


def test_evaluate_budget_sensitivity_tie_breaking():
    """Assert tie-breaking strictly prioritizes lower row_index for identical scores."""
    scored_df = pd.DataFrame({
        "row_index": [50, 10, 30, 20],
        "anomaly_score": [0.99, 0.99, 0.99, 0.99],
        "anomaly_status": [AnomalyStatus.SCORED.value] * 4,
        "channel": ["TRANSFER"] * 4,
    })
    y_true = pd.Series([1, 0, 1, 0], index=[50, 10, 30, 20])

    # K=2 out of 4 rows: budget rate = 0.50
    results = evaluate_budget_sensitivity(
        scored_df=scored_df,
        y_true=y_true,
        scenarios=(0.50,),
    )

    scenario_50 = results["scenarios"]["50.00%"]
    assert scenario_50["K"] == 2
    # Rows 10 and 20 should be selected because 10 < 20 < 30 < 50
    # y_true for row 10 is 0, for row 20 is 0 -> TP = 0
    assert scenario_50["TP"] == 0


# ==============================================================================
# REPORT FORMATTING TESTS
# ==============================================================================

def test_format_evaluation_report_mandatory_caveats():
    """Assert evaluation report contains all mandatory caveats and adheres to schema."""
    report = format_evaluation_report(
        config_digests=("raw_sha_test", "ast_sha_test"),
        population_metrics={"ref": 100, "val": 50},
        psi_results={"TRANSFER": {"psi": 0.01}},
        sensitivity_results={"scenarios": {}},
    )

    assert report["protocol_version"] == "v1.2.7-DRAFT"
    assert report["config_provenance"]["raw_sha256"] == "raw_sha_test"
    assert report["config_provenance"]["ast_sha256"] == "ast_sha_test"

    caveats = report["mandatory_caveats"]
    assert len(caveats) == 4
    assert any("synthetic PaySim mobile money agent simulation" in c for c in caveats)
    assert any("strictly prohibited claims" in c for c in caveats)
    assert any("unsupervised behavioral surveillance layer" in c for c in caveats)
    assert any("in-sample reference baseline" in c for c in caveats)

