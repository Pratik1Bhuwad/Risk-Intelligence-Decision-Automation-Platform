"""
Tests for FeatureQualityValidator.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.validator import FeatureQualityValidator
from src.features.pipeline import FeaturePipeline


def test_validator_on_clean_data(synthetic_df):
    pipeline = FeaturePipeline()
    feature_df = pipeline.transform(synthetic_df, include_target_label=False)

    validator = FeatureQualityValidator()
    is_valid, report = validator.validate(synthetic_df, feature_df)

    assert is_valid is True
    assert len(report["errors"]) == 0
    assert report["metrics"]["feature_columns_count"] > 0
    assert report["metrics"]["null_cells_total"] == 0
    assert report["metrics"]["inf_cells_total"] == 0


def test_validator_fails_on_injected_forbidden_column(synthetic_df):
    pipeline = FeaturePipeline()
    feature_df = pipeline.transform(synthetic_df, include_target_label=False)

    # Infiltrate a forbidden post-event column
    feature_df["newbalanceOrig"] = synthetic_df["newbalanceOrig"]

    validator = FeatureQualityValidator()
    is_valid, report = validator.validate(synthetic_df, feature_df)

    assert is_valid is False
    assert any("CRITICAL LEAKAGE" in err for err in report["errors"])


def test_validator_fails_on_nulls(synthetic_df):
    pipeline = FeaturePipeline()
    feature_df = pipeline.transform(synthetic_df, include_target_label=False)

    # Inject NaN
    feature_df.loc[0, "amount"] = np.nan

    validator = FeatureQualityValidator()
    is_valid, report = validator.validate(synthetic_df, feature_df)

    assert is_valid is False
    assert any("Null values detected" in err for err in report["errors"])


def test_validator_fails_on_infinite(synthetic_df):
    pipeline = FeaturePipeline()
    feature_df = pipeline.transform(synthetic_df, include_target_label=False)

    # Inject inf
    feature_df.loc[0, "amount"] = np.inf

    validator = FeatureQualityValidator()
    is_valid, report = validator.validate(synthetic_df, feature_df)

    assert is_valid is False
    assert any("Infinite values detected" in err for err in report["errors"])
