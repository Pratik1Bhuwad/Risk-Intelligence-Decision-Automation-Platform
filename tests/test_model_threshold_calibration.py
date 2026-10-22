"""
Tests for ThresholdOptimizer and RiskCalibrator.
"""

import numpy as np
import pandas as pd
import pytest

from src.models.calibration import RiskCalibrator
from src.models.threshold import ThresholdOptimizer


def test_threshold_optimizer_on_synthetic_data():
    y_true = pd.Series([0, 0, 0, 0, 1, 1, 1, 1])
    # Well separated probabilities
    y_prob = np.array([0.05, 0.1, 0.15, 0.2, 0.8, 0.85, 0.9, 0.95])

    optimizer = ThresholdOptimizer(target_metric="f1")
    optimizer.fit(y_true, y_prob)

    assert 0.2 < optimizer.optimal_threshold <= 0.85
    assert optimizer.low_threshold <= optimizer.optimal_threshold
    assert optimizer.high_threshold >= optimizer.optimal_threshold

    # Single decision mapping
    dec_low, lvl_low, flag_low = optimizer.classify_probability(0.05)
    assert dec_low == "APPROVE"
    assert lvl_low == "LOW"
    assert flag_low == 0

    dec_high, lvl_high, flag_high = optimizer.classify_probability(0.95)
    assert dec_high == "MANUAL_INVESTIGATION"
    assert lvl_high == "HIGH"
    assert flag_high == 1

    # Batch decision mapping
    batch_res = optimizer.classify_batch(y_prob)
    assert len(batch_res) == 8
    assert list(batch_res.columns) == [
        "risk_score",
        "risk_score_100",
        "risk_level",
        "decision",
        "is_fraud_flagged",
    ]


def test_risk_calibrator_sigmoid():
    y_true = pd.Series([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.25, 0.3, 0.7, 0.75, 0.8, 0.9])

    calibrator = RiskCalibrator(method="sigmoid")
    calibrator.fit(y_true, y_prob)

    cal_probs = calibrator.predict_proba(y_prob)
    assert len(cal_probs) == 8
    assert np.all(cal_probs >= 0.0) and np.all(cal_probs <= 1.0)
    assert calibrator.diagnostics["calibrated_brier_score"] <= calibrator.diagnostics["raw_brier_score"] + 0.05


def test_threshold_operating_policy_monotonicity_and_invariance():
    """
    Verify that higher risk probabilities strictly receive equal or more severe actions
    (APPROVE <= MONITOR <= MANUAL_INVESTIGATION) and that binary flag matches the high tier
    when optimal_threshold == high_threshold.
    """
    optimizer = ThresholdOptimizer(target_metric="f1")
    y_true = pd.Series([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.0001, 0.0002, 0.0003, 0.0004, 0.98, 0.985, 0.99, 0.995])
    optimizer.fit(y_true, y_prob)

    assert optimizer.optimal_threshold > 0.50
    assert optimizer.high_threshold == optimizer.optimal_threshold
    assert optimizer.low_threshold <= 0.30

    test_probs = np.array([0.0001, 0.15, 0.30, 0.50, 0.70, 0.985])
    batch_res = optimizer.classify_batch(test_probs)

    # Monotonicity checks
    severity_map = {"APPROVE": 1, "MONITOR": 2, "MANUAL_INVESTIGATION": 3}
    severities = [severity_map[d] for d in batch_res["decision"]]
    assert severities == sorted(severities), "Decisions must be monotonic with respect to probability"

    # Flag alignment
    assert np.all(batch_res["is_fraud_flagged"] == (batch_res["decision"] == "MANUAL_INVESTIGATION").astype(int))


def test_exact_threshold_boundary_conditions():
    """
    Verify exact mathematical boundary conditions:
    - Below low_threshold: APPROVE
    - Exactly at low_threshold: MONITOR
    - Just below high_threshold: MONITOR
    - Exactly at high_threshold: MANUAL_INVESTIGATION
    """
    optimizer = ThresholdOptimizer()
    optimizer.low_threshold = 0.30
    optimizer.high_threshold = 0.9771
    optimizer.optimal_threshold = 0.9771

    # Single classification
    dec, lvl, flag = optimizer.classify_probability(0.299999)
    assert dec == "APPROVE" and lvl == "LOW" and flag == 0

    dec, lvl, flag = optimizer.classify_probability(0.300000)
    assert dec == "MONITOR" and lvl == "MEDIUM" and flag == 0

    dec, lvl, flag = optimizer.classify_probability(0.977099)
    assert dec == "MONITOR" and lvl == "MEDIUM" and flag == 0

    dec, lvl, flag = optimizer.classify_probability(0.977100)
    assert dec == "MANUAL_INVESTIGATION" and lvl == "HIGH" and flag == 1

    # Batch classification
    boundary_probs = np.array([0.299999, 0.300000, 0.977099, 0.977100])
    res = optimizer.classify_batch(boundary_probs)
    assert list(res["decision"]) == ["APPROVE", "MONITOR", "MONITOR", "MANUAL_INVESTIGATION"]
    assert list(res["risk_level"]) == ["LOW", "MEDIUM", "MEDIUM", "HIGH"]
    assert list(res["is_fraud_flagged"]) == [0, 0, 0, 1]
