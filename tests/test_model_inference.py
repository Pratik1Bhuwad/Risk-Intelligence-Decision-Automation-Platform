"""
Tests for RiskPredictor inference interface and contracts.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from src.features.metadata import FEATURE_CATALOG
from src.models.inference import RiskPredictor
from src.models.preprocessor import ModelFeaturePreprocessor
from src.models.threshold import ThresholdOptimizer


@pytest.fixture
def mock_predictor() -> RiskPredictor:
    features = list(FEATURE_CATALOG.keys())
    # Create small dummy training data
    df_train = pd.DataFrame({f: np.linspace(0, 1, 10) for f in features})
    y_train = pd.Series([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])

    prep = ModelFeaturePreprocessor(scale_numeric=False)
    prep.fit(df_train)

    model = DummyClassifier(strategy="constant", constant=1)
    model.fit(df_train, y_train)

    opt = ThresholdOptimizer()
    opt.optimal_threshold = 0.5
    opt.low_threshold = 0.3
    opt.high_threshold = 0.7

    return RiskPredictor(
        model=model,
        preprocessor=prep,
        threshold_optimizer=opt,
        metadata={"model_name": "test_dummy"},
    )


def test_risk_predictor_single_dict_inference(mock_predictor: RiskPredictor):
    features = list(FEATURE_CATALOG.keys())
    record = {f: 0.5 for f in features}

    prob = mock_predictor.predict_proba(record)
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0

    score = mock_predictor.predict_score(record)
    assert isinstance(score, int)
    assert 0 <= score <= 100

    decision = mock_predictor.predict_decision(record)
    assert isinstance(decision, dict)
    assert decision["decision"] in ("APPROVE", "MONITOR", "MANUAL_INVESTIGATION")
    assert decision["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert decision["is_fraud_flagged"] in (0, 1)


def test_risk_predictor_batch_inference(mock_predictor: RiskPredictor):
    features = list(FEATURE_CATALOG.keys())
    df = pd.DataFrame({f: [0.1, 0.5, 0.9] for f in features})

    probs = mock_predictor.predict_proba(df)
    assert len(probs) == 3

    scores = mock_predictor.predict_score(df)
    assert len(scores) == 3

    decisions = mock_predictor.predict_decision(df)
    assert isinstance(decisions, pd.DataFrame)
    assert len(decisions) == 3
    assert set(decisions.columns) == {
        "risk_score",
        "risk_score_100",
        "risk_level",
        "decision",
        "is_fraud_flagged",
    }


def test_risk_predictor_rejects_missing_features(mock_predictor: RiskPredictor):
    incomplete_record = {"amount": 500.0}
    with pytest.raises(ValueError, match="Missing required model input features"):
        mock_predictor.predict_decision(incomplete_record)


def test_risk_predictor_rejects_forbidden_columns(mock_predictor: RiskPredictor):
    features = list(FEATURE_CATALOG.keys())
    record = {f: 0.5 for f in features}
    record["newbalanceOrig"] = 1000.0  # forbidden leakage column
    with pytest.raises(ValueError, match="Prediction Security Violation"):
        mock_predictor.predict_decision(record)
