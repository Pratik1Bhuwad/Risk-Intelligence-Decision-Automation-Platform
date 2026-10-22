"""
Tests for ModelFeaturePreprocessor and leakage rejection.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.metadata import FEATURE_CATALOG
from src.models.preprocessor import ModelFeaturePreprocessor


def test_model_preprocessor_column_order_and_scaling():
    features = list(FEATURE_CATALOG.keys())
    data = {f: [1.0, 2.0, 3.0] for f in features}
    df = pd.DataFrame(data)

    prep = ModelFeaturePreprocessor(scale_numeric=True)
    prep.fit(df)

    res = prep.transform(df)
    assert list(res.columns) == features
    # Check that scaled data has mean close to 0
    assert np.allclose(res.mean().values, 0.0, atol=1e-5)


def test_model_preprocessor_rejects_missing_columns():
    features = list(FEATURE_CATALOG.keys())[:-2]  # drop 2 features
    df = pd.DataFrame({f: [1.0] for f in features})

    prep = ModelFeaturePreprocessor()
    with pytest.raises(ValueError, match="Missing required model input features"):
        prep.fit(df)


def test_model_preprocessor_rejects_forbidden_leakage_columns():
    features = list(FEATURE_CATALOG.keys())
    data = {f: [1.0] for f in features}
    data["newbalanceOrig"] = [100.0]  # Prohibited post-event column

    df = pd.DataFrame(data)
    prep = ModelFeaturePreprocessor()
    with pytest.raises(ValueError, match="Security/Leakage Violation"):
        prep.fit(df)


def test_model_preprocessor_rejects_nulls_and_infinities():
    features = list(FEATURE_CATALOG.keys())
    data = {f: [1.0, np.nan] for f in features}
    df = pd.DataFrame(data)

    prep = ModelFeaturePreprocessor()
    prep.fit(pd.DataFrame({f: [1.0, 2.0] for f in features}))

    with pytest.raises(ValueError, match="Input features contain NaN/null"):
        prep.transform(df)
