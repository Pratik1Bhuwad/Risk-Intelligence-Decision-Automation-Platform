"""
Unit tests for Phase 05 IsolationForest Outlier Detector.
"""

import numpy as np
import pytest

from src.anomaly.detector import IsolationForestDetector


def test_detector_instantiation_and_fit():
    """Verify detector initialization and fitting."""
    np.random.seed(42)
    X = np.random.normal(loc=0.0, scale=1.0, size=(100, 5))

    detector = IsolationForestDetector(n_estimators=50, random_state=42)
    detector.fit(X)
    assert detector.is_fitted
    assert detector.n_features_in_ == 5


def test_score_direction():
    """
    Verify score direction: s_raw(x) = -score_samples(x).
    Higher scores must indicate more anomalous observations.
    """
    np.random.seed(42)
    # 200 normal points near 0
    X_train = np.random.normal(loc=0.0, scale=0.5, size=(200, 2))
    detector = IsolationForestDetector(n_estimators=100, random_state=42)
    detector.fit(X_train)

    normal_point = np.array([[0.1, -0.1]])
    extreme_outlier = np.array([[50.0, 50.0]])

    score_normal = detector.score_samples(normal_point)[0]
    score_outlier = detector.score_samples(extreme_outlier)[0]

    # Extreme outlier must receive higher anomaly score under negated convention
    assert score_outlier > score_normal, (
        f"Score direction violation: outlier score {score_outlier} must be > normal score {score_normal}"
    )


def test_deterministic_scoring():
    """Verify that identical input matrices yield bitwise-identical scores."""
    np.random.seed(42)
    X_train = np.random.normal(size=(100, 4))
    X_test = np.random.normal(size=(20, 4))

    d1 = IsolationForestDetector(n_estimators=50, random_state=42, n_jobs=1)
    d1.fit(X_train)
    scores1 = d1.score_samples(X_test)

    d2 = IsolationForestDetector(n_estimators=50, random_state=42, n_jobs=1)
    d2.fit(X_train)
    scores2 = d2.score_samples(X_test)

    np.testing.assert_array_equal(scores1, scores2)


def test_reject_non_finite_inputs():
    """Verify rejection of NaN / Inf in fit and scoring."""
    detector = IsolationForestDetector(n_estimators=10, random_state=42)
    X_bad = np.array([[1.0, np.nan], [2.0, 3.0]])
    with pytest.raises(ValueError, match="non-finite values"):
        detector.fit(X_bad)

    X_good = np.array([[1.0, 2.0], [3.0, 4.0]])
    detector.fit(X_good)
    with pytest.raises(ValueError, match="non-finite values"):
        detector.score_samples(X_bad)

