"""
Tests for end-to-end Feature Pipeline execution.
"""

import json
import os
import pandas as pd
import pytest

from src.features.pipeline import FeaturePipeline


def test_feature_pipeline_run_end_to_end(synthetic_csv_file, tmp_path):
    out_dir = str(tmp_path / "processed_test")
    pipeline = FeaturePipeline()

    manifest = pipeline.run(
        raw_csv_path=synthetic_csv_file,
        output_dir=out_dir,
        nrows=None,
        save_csv=True,
        save_parquet=False,
        include_target_label=True,
    )

    assert manifest["row_count"] == 10
    assert manifest["has_target_label"] is True
    assert manifest["feature_count"] == 36
    assert len(manifest["feature_columns"]) == 36

    # Check manifest file
    manifest_file = os.path.join(out_dir, "feature_manifest.json")
    assert os.path.exists(manifest_file)
    with open(manifest_file, "r") as f:
        loaded_manifest = json.load(f)
    assert loaded_manifest["row_count"] == 10
    assert loaded_manifest["feature_count"] == 36

    # Check output CSV
    csv_file = manifest["output_files"]["csv"]
    assert os.path.exists(csv_file)
    df_out = pd.read_csv(csv_file)
    assert len(df_out) == 10
    assert "isFraud" in df_out.columns
    assert len(df_out.columns) == 37  # 36 features + 1 target label
    assert "dest_prior_tx_count" in df_out.columns
    assert "is_full_balance_drain" in df_out.columns

    # Check feature catalog export
    cat_file = manifest["output_files"]["catalog_csv"]
    assert os.path.exists(cat_file)
    cat_df = pd.read_csv(cat_file)
    assert len(cat_df) == 36


def test_feature_catalog_exact_match_with_pipeline_features(synthetic_csv_file):
    """
    Verify that FEATURE_CATALOG and pipeline output schema agree 100% on feature count (36),
    that every catalog entry is implemented, no unimplemented feature is listed,
    and raw identifiers/target are strictly excluded from the model feature matrix.
    """
    from src.features.metadata import FEATURE_CATALOG

    df_raw = pd.read_csv(synthetic_csv_file)
    pipeline = FeaturePipeline()

    # 1. Without target: exactly 36 model input features
    df_features = pipeline.transform(df_raw, include_target_label=False)
    assert len(df_features.columns) == 36
    assert len(FEATURE_CATALOG) == 36
    assert set(df_features.columns) == set(FEATURE_CATALOG.keys())

    # Raw identifiers and target must NOT be in feature columns
    excluded_columns = {"isFraud", "nameOrig", "nameDest", "step", "newbalanceOrig", "newbalanceDest", "oldbalanceDest", "isFlaggedFraud"}
    assert excluded_columns.isdisjoint(set(df_features.columns))

    # 2. With target: exactly 37 columns (36 model features + 1 target)
    df_with_target = pipeline.transform(df_raw, include_target_label=True)
    assert len(df_with_target.columns) == 37
    assert "isFraud" in df_with_target.columns
    assert set(df_with_target.columns) - {"isFraud"} == set(FEATURE_CATALOG.keys())

