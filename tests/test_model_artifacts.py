"""
Tests for Model Artifact saving, loading, and reload consistency.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.features.metadata import FEATURE_CATALOG
from src.models.artifacts import ModelArtifactManager
from src.models.calibration import RiskCalibrator
from src.models.inference import RiskPredictor
from src.models.preprocessor import ModelFeaturePreprocessor
from src.models.threshold import ThresholdOptimizer


def test_artifact_save_load_and_prediction_consistency(tmp_path):
    artifact_dir = str(tmp_path / "test_model_artifact")

    features = list(FEATURE_CATALOG.keys())
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(20, len(features)), columns=features)
    y = pd.Series(np.random.randint(0, 2, 20))

    prep = ModelFeaturePreprocessor(scale_numeric=True)
    prep.fit(X)
    X_tf = prep.transform(X)

    model = LogisticRegression(random_state=42)
    model.fit(X_tf, y)

    raw_probs = model.predict_proba(X_tf)[:, 1]

    calibrator = RiskCalibrator(method="sigmoid")
    calibrator.fit(y, raw_probs)

    cal_probs = calibrator.predict_proba(raw_probs)

    thresh_opt = ThresholdOptimizer()
    thresh_opt.fit(y, cal_probs)

    metadata = {
        "model_name": "test_lr",
        "version": "1.0.0",
        "features": features,
    }

    # Save
    saved_paths = ModelArtifactManager.save_bundle(
        artifact_dir=artifact_dir,
        model=model,
        preprocessor=prep,
        calibrator=calibrator,
        threshold_optimizer=thresh_opt,
        metadata=metadata,
    )
    assert "bundle_path" in saved_paths
    assert "metadata_path" in saved_paths

    # Reload via RiskPredictor
    predictor = RiskPredictor.load(artifact_dir)

    # Test identical predictions
    original_probs = cal_probs
    reloaded_probs = predictor.predict_proba(X)

    assert np.allclose(original_probs, reloaded_probs, atol=1e-7)

    # Verify metadata is loaded
    loaded_meta = predictor.get_metadata()
    assert loaded_meta["model_name"] == "test_lr"
    assert loaded_meta["version"] == "1.0.0"
