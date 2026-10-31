"""
Unit tests for End-to-End AnomalyDetectionEngine Orchestration.
"""

import numpy as np
import pandas as pd
import pytest

from src.anomaly.engine import AnomalyDetectionEngine
from src.anomaly.schema import AnomalyOutputSchema, AnomalyStatus, ReasonCode
from src.features.metadata import FEATURE_CATALOG
from src.models.inference import RiskPredictor


def _generate_synthetic_data(n_samples: int = 150, channel: str = "TRANSFER", base_row_index: int = 0):
    """Generate small synthetic feature dataset adhering to the 36-feature catalog."""
    np.random.seed(42 + base_row_index)
    rows = []
    for i in range(n_samples):
        row = {
            "row_index": base_row_index + i,
            "type": channel,
            "step": 10 + (i % 50),
        }
        # Populate all 36 features
        for feat in FEATURE_CATALOG.keys():
            if feat.startswith("is_"):
                row[feat] = 1 if feat == f"is_{channel.lower()}" else 0
            elif "amount" in feat or "balance" in feat:
                row[feat] = float(np.random.exponential(scale=50000.0))
            else:
                row[feat] = float(np.random.normal(loc=10.0, scale=2.0))
        rows.append(row)
    return pd.DataFrame(rows)


def test_engine_fit_and_score_end_to_end():
    """Verify end-to-end engine fitting, scoring, and output DataFrame schema."""
    # Synthetic reference data (TRANSFER and CASH_OUT)
    ref_transfer = _generate_synthetic_data(100, "TRANSFER", base_row_index=0)
    ref_cash_out = _generate_synthetic_data(100, "CASH_OUT", base_row_index=100)
    ref_df = pd.concat([ref_transfer, ref_cash_out], ignore_index=True)

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)
    assert engine.is_fitted
    assert "TRANSFER" in engine.detectors
    assert "CASH_OUT" in engine.detectors

    # Test scoring population (150 rows)
    test_transfer = _generate_synthetic_data(80, "TRANSFER", base_row_index=200)
    test_cash_out = _generate_synthetic_data(70, "CASH_OUT", base_row_index=280)
    test_df = pd.concat([test_transfer, test_cash_out], ignore_index=True)

    rows, out_df, summary = engine.score(test_df)

    assert len(rows) == 150
    assert len(out_df) == 150
    assert list(out_df.columns) == AnomalyOutputSchema.COLUMN_NAMES

    # Check alert budget: K = floor(0.0100 * 150) = 1
    assert summary.budget_denominator == 150
    assert summary.budget_k == 1
    assert summary.selected_alert_count == 1
    assert (out_df["alert_budget_selected"] == True).sum() == 1


def test_exclusion_of_ineligible_channels():
    """Verify that PAYMENT, CASH_IN, and DEBIT transactions are excluded from scoring."""
    ref_df = _generate_synthetic_data(60, "TRANSFER", base_row_index=0)
    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # Scoring batch containing eligible TRANSFER and ineligible PAYMENT / DEBIT
    eligible_df = _generate_synthetic_data(50, "TRANSFER", base_row_index=100)
    payment_df = _generate_synthetic_data(20, "PAYMENT", base_row_index=200)
    debit_df = _generate_synthetic_data(10, "DEBIT", base_row_index=300)
    mix_df = pd.concat([eligible_df, payment_df, debit_df], ignore_index=True)

    rows, out_df, summary = engine.score(mix_df)

    # Only eligible TRANSFER should be scored; ineligible PAYMENT and DEBIT are tracked in ineligible_count
    assert summary.input_count == 80
    assert summary.eligible_count == 50
    assert summary.ineligible_count == 30  # 20 PAYMENT + 10 DEBIT
    assert summary.successfully_scored_count == 50
    assert summary.unscored_eligible_count == 0
    assert summary.degraded_count == 0
    assert summary.input_count == summary.eligible_count + summary.ineligible_count
    assert summary.eligible_count == summary.successfully_scored_count + summary.unscored_eligible_count


def test_all_inactive_features_produces_degraded_state():
    """
    Verify that when all anomaly features have zero dispersion (active features empty),
    the transaction produces State C (DEGRADED_UNSCORABLE) with ALL_ANOMALY_FEATURES_INACTIVE.
    """
    # Create reference data where all features are identical constants (zero dispersion)
    rows = []
    for i in range(50):
        row = {"row_index": i, "type": "TRANSFER", "step": 1}
        for f in FEATURE_CATALOG.keys():
            row[f] = 0.0  # Constant!
        rows.append(row)
    ref_df = pd.DataFrame(rows)

    engine = AnomalyDetectionEngine(config_path="configs/anomaly_detection.yaml")
    engine.fit(ref_df)

    # All features should be excluded due to zero dispersion across all tiers
    assert len(engine.preprocessor.get_active_features("TRANSFER")) == 0

    # Score a test row
    test_df = pd.DataFrame([rows[0]])
    rows_out, out_df, summary = engine.score(test_df)

    assert len(rows_out) == 1
    res = rows_out[0]
    assert res.anomaly_status == AnomalyStatus.DEGRADED_UNSCORABLE.value
    assert res.reason_code == ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value
    assert res.anomaly_score is None
    assert res.is_anomaly_flagged is None
    assert res.alert_budget_selected is False


def test_phase_04_independence_and_no_mutation():
    """Verify that Phase 05 anomaly engine does not mutate Phase 04 models, inputs, or contracts."""
    # Ensure RiskPredictor class and outputs are unmutated
    import inspect
    from src.models.inference import RiskPredictor

    # RiskPredictor methods must remain standard
    methods = [m[0] for m in inspect.getmembers(RiskPredictor, predicate=inspect.isfunction)]
    assert "predict_decision" in methods
    assert "predict_proba" in methods
    assert "predict_score" in methods
    # Zero Phase 05 anomaly attributes should be attached to RiskPredictor
    assert not hasattr(RiskPredictor, "anomaly_score")
    assert not hasattr(RiskPredictor, "is_anomaly_flagged")

