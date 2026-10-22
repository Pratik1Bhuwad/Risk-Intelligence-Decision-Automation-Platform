"""
Tests for Temporal Splitting module.
"""

import pandas as pd
import pytest

from src.models.split import TemporalSplitter


def test_temporal_splitter_boundaries():
    with pytest.raises(ValueError, match="train_max_step"):
        TemporalSplitter(train_max_step=500, val_max_step=400)


def test_temporal_splitter_monotonicity_and_disjointness():
    # Synthetic dataframe with 10 steps
    df = pd.DataFrame(
        {
            "step": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "feature_1": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            "isFraud": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )

    splitter = TemporalSplitter(
        train_max_step=4,
        val_max_step=7,
        test_max_step=10,
    )

    (X_tr, y_tr), (X_val, y_val), (X_te, y_te), summaries = splitter.split(df)

    assert len(X_tr) == 4
    assert len(X_val) == 3
    assert len(X_te) == 3

    assert summaries["train"].max_step == 4
    assert summaries["val"].min_step == 5
    assert summaries["val"].max_step == 7
    assert summaries["test"].min_step == 8
    assert summaries["test"].max_step == 10

    # Ensure target column is NOT in X
    assert "isFraud" not in X_tr.columns
    assert "isFraud" not in X_val.columns
    assert "isFraud" not in X_te.columns


def test_temporal_splitter_reconstruction_from_cyclical_features():
    # If step is missing, it should reconstruct step = day_of_simulation * 24 + hour_of_day
    df = pd.DataFrame(
        {
            "day_of_simulation": [0, 0, 1, 1],
            "hour_of_day": [10, 15, 2, 5],
            "feature_a": [1, 2, 3, 4],
            "isFraud": [0, 1, 0, 1],
        }
    )
    # Expected steps: 10, 15, 26, 29
    splitter = TemporalSplitter(train_max_step=15, val_max_step=27, test_max_step=30)
    (X_tr, y_tr), (X_val, y_val), (X_te, y_te), summaries = splitter.split(df)

    assert len(X_tr) == 2
    assert len(X_val) == 1
    assert len(X_te) == 1
